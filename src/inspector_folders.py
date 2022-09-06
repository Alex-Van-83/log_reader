import os
import json
from db_model import *
from multiprocessing import Process, JoinableQueue
import time
from datetime import datetime
import loger
import re


task_for_read_file_queue = JoinableQueue()
procs = []


def write_log(report_text):
    loger.write_log('log', f'{report_text} {datetime.now()} {os.getpid()} \n')


def file_is_completed(filename):
    try:
        os.rename(filename, filename)
        return True
    except OSError:
        return False


def file_last_position(filename):
    try:
        with open(filename, 'a', encoding='utf-8') as file_handler:
            return file_handler.tell()
    except FileNotFoundError:
        return 0


def take_files(file_path, deep, mask, new_files, files_for_processing):
    for fs_object in os.scandir(file_path):
        new_path = os.path.abspath(fs_object.path)
        if fs_object.is_dir() and deep:
            take_files(new_path, deep - 1, mask, new_files, files_for_processing)
        elif fs_object.is_file():
            if re.match(mask, fs_object.name):
                file_info = fs_object.stat()
                if new_path in files_for_processing:
                    FileForProcessing.update(size=round(file_info.st_size / 1024),
                                             last_position=file_last_position(new_path),
                                             completed=file_is_completed(new_path)) \
                                     .where(
                                            FileForProcessing.full_path == new_path
                                        ) \
                                    .execute()

                    files_for_processing.remove(new_path)
                else:
                    new_files.append({'full_path': new_path,
                                      'size': round(file_info.st_size / 1024),
                                      'file_name': fs_object.name,
                                      'directory': os.path.split(file_path)[-1],
                                      'last_position': file_last_position(new_path),
                                      'completed': file_is_completed(new_path)
                                      })


def inspect_folders():
    with core_db:
        points = MonitoringPoint.select(
            MonitoringPoint.id,
            MonitoringPoint.settings
        ) \
            .where(
            MonitoringPoint.monitoring == True
        )
        for point in points:
            files_for_processing = FileForProcessing.select(
                FileForProcessing.full_path
            ).where(
                (FileForProcessing.date_lost.is_null(True))  # not losted
                &
                (FileForProcessing.monitoring_point == point.id)
            )
            settings = json.loads(point.settings)
            lost_files = []
            new_files = []
            for file in files_for_processing:
                lost_files.append(file.full_path)
            take_files(settings['PATH'], settings['DEEP'], settings['FILTER'], new_files, lost_files)
            for lost_file in lost_files:
                FileForProcessing.update(timestamp_lost=timestamp(),
                                         date_lost=datetime.now()) \
                    .where(
                    FileForProcessing.full_path == lost_file) \
                    .execute()
            for new_files_for_processing in new_files:
                new_files_for_processing['monitoring_point'] = point.id
            if len(new_files):
                FileForProcessing.insert_many(new_files).execute()
    write_log('inspect_folders')


def create_task_for_read_file():
    with core_db:
        file_without_task = FileForProcessing\
            .select(
                    FileForProcessing.id,
                    FileForProcessing.file_name,
                    FileForProcessing.completed,
                    FileForProcessing.last_position)\
            .join(TaskForProcessingFile, JOIN.LEFT_OUTER, on=(FileForProcessing.id == TaskForProcessingFile.file))\
            .where(
                (FileForProcessing.completed == True)
                &
                (FileForProcessing.date_lost.is_null(True))
                &
                (TaskForProcessingFile.id.is_null(True))
            )
        new_tasks = []
        for file_info in file_without_task:
            new_tasks.append({'file_id': file_info.id})
        if len(new_tasks):
            TaskForProcessingFile.insert_many(new_tasks).execute()
    write_log('create_task_for_read_file')


def start_read_file_by_task():

    tasks_for_processing = TaskForProcessingFile \
        .select(TaskForProcessingFile.id)\
        .join(ReadPartFile,
              JOIN.LEFT_OUTER,
              on=(TaskForProcessingFile.id == ReadPartFile.task)) \
        .join(FileForProcessing,
              JOIN.LEFT_OUTER,
              on=(TaskForProcessingFile.file == FileForProcessing.id)) \
        .where((FileForProcessing.date_lost.is_null(True))
               &
               (ReadPartFile.id.is_null(True)))

    for task in tasks_for_processing:
        take_event_from_file({'task': task.id})
        # task_for_read_file_queue.put({'task': task.id})

    # read_file(task_for_read_file_queue)

    # fork = Process(target=read_file, args=(task_for_read_file_queue,))
    # fork.start()
    # task_for_read_file_queue.join()
    write_log('start_read_file_by_task')


def read_file(queue):

    while not queue.empty():
        task_info = queue.get()
        take_event_from_file(task_info)
        queue.task_done()


def flash_cash(cash, events_array):
    if len(cash):
        events_array.append(''.join(cash))
        cash.clear()


def append_event(cash, limit_events_array, events_array):
    flash_cash(cash, events_array)
    return limit_control(events_array, limit_events_array)


def limit_control(events_array, limit_events_array):
    processing_time_start = time.perf_counter()
    if len(events_array) >= limit_events_array:
        # TODO отправка событий для обработки
        events_array.clear()
    return time.perf_counter() - processing_time_start


def get_position_in_file(file, offset, event_regexp_begin):
    file.seek(offset)
    new_position = offset
    if offset > 0:
        while True:
            line = file.readline()
            if event_regexp_begin.match(line):
                file.seek(new_position)
                break
            new_position = file.tell()
    return new_position


def take_event_from_file(task_info):

    task = TaskForProcessingFile.get(task_info['task'])
    filename = task.file.full_path
    start_position = task.start_position
    end_position = start_position + task.max_offset

    read_part_file = ReadPartFile(file=task.file, task=task, start_position=start_position, executor=os.getpid())

    limit_events_array = 100000

    settings = json.loads(task.file.monitoring_point.settings)['EVENT']
    event_multi_line = settings['MULTI_LINE']
    event_regexp_begin = re.compile(settings['REGEXP_BEGIN'])

    start = time.perf_counter()
    with open(filename, "r", encoding="utf-8") as file:
        get_position_in_file(file, start_position, event_regexp_begin)
        if end_position == 0:
            take_event_from_text(event_multi_line, event_regexp_begin, file, limit_events_array, read_part_file)
        else:
            end_position = get_position_in_file(file, end_position, event_regexp_begin)
            start_position = get_position_in_file(file, start_position, event_regexp_begin)
            text = file.read(end_position - start_position).split()
            take_event_from_text(event_multi_line, event_regexp_begin, text, limit_events_array, read_part_file)
        read_part_file.end_position = file.tell()

    read_part_file.duration = time.perf_counter() - start
    read_part_file.save()


def take_event_from_text(event_multi_line, event_regexp_begin, file, limit_events_array, read_part_file):

    cash = []
    row_count = 0
    events_array = []
    event_count = 0
    processing_time_total = 0

    for line in file:
        row_count += 1
        if event_multi_line == 1:
            if event_regexp_begin.match(line):
                event_count += 1
                processing_time_total += append_event(cash, limit_events_array, events_array)
                cash.append(line.rstrip())
            else:
                cash.append(line.rstrip())
        else:
            events_array.append(line.rstrip())
            processing_time_total += limit_control(events_array, limit_events_array)

    processing_time_total += append_event(cash, 0, events_array)

    read_part_file.row_count = row_count
    read_part_file.event_count = event_count


def add_monitoring_point():
    new_monitoring_point = MonitoringPoint()
    new_monitoring_point.description = 'логи тех. журнала 1с'
    new_monitoring_point.monitoring = True
    new_monitoring_point.settings = '{"PATH":"E:/1cTJ/",' \
                                    '"DEEP":-1,' \
                                    '"FILTER":"[0-9]{8}.log",' \
                                    '"EVENT":{ "MULTI_LINE":1,' \
                                    '          "REGEXP_BEGIN":"^[0-9]{2}:[0-9]{2}.[0-9]+-[0-9]+",' \
                                    '           "PART_FOR_READ":0}' \
                                    '}'
    new_monitoring_point.save()

if __name__ == '__main__':
    take_event_from_file({'task': '1568'})
     # add_monitoring_point()
     # inspect_folders()
     # create_task_for_read_file()
     # start_read_file_by_task()

