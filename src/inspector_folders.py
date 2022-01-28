import os
import json
from db_model import *


def file_is_completed(filename):
    try:
        os.rename(filename, filename)
        return True
    except [FileExistsError, IsADirectoryError, NotADirectoryError]:
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
            if fs_object.name.find(mask):
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
                                      'description': fs_object.name,
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
            MonitoringPoint.monitoring is True
        )
        for point in points:
            settings = json.loads(point.settings)
            files_for_processing = FileForProcessing.select(
                FileForProcessing.full_path
            ).where(
                (FileForProcessing.date_lost.is_null(True))  # not losted
                &
                ((FileForProcessing.date_scheduled.is_null(True))  # not scheduled
                 |
                 (FileForProcessing.date_processed.is_null(True)))  # not processed
                &
                (FileForProcessing.basic_directory == point.id)
            )
            lost_files = []
            new_files = []
            for file in files_for_processing:
                lost_files.append(file.full_path)
            take_files(settings['PATH'], settings['DEEP'], settings['FILTER'], new_files, lost_files)
            for lost_file in lost_files:
                FileForProcessing.update(timestamp_lost=timestamp(),
                                         date_lost=datetime.now()) \
                    .where(
                    FileForProcessing.full_path == lost_file
                ) \
                    .execute()
            for new_files_for_processing in new_files:
                new_files_for_processing['basic_directory_id'] = point.id
            if len(new_files):
                FileForProcessing.insert_many(new_files).execute()


def create_task_for_read_file():
    with core_db:
        file_without_task = FileForProcessing\
            .select(
                    FileForProcessing.id,
                    FileForProcessing.description,
                    FileForProcessing.completed,
                    FileForProcessing.last_position)\
            .join(TaskForProcessingFile, JOIN.LEFT_OUTER, on=(FileForProcessing.id == TaskForProcessingFile.file))\
            .where(
                (FileForProcessing.completed is True)
                &
                (FileForProcessing.date_lost.is_null(True))
                &
                (TaskForProcessingFile.id.is_null(True))
            )
        new_tasks = []
        for file_info in file_without_task:
            new_tasks.append({'file': file_info.id,
                              'description': f' {file_info.description}'})
        if len(new_tasks):
            TaskForProcessingFile.insert_many(new_tasks).execute()


def start_read_file_by_task():

    query = Select(columns=[FileForProcessing.full_path,
                            TaskForProcessingFile.id,
                            TaskForProcessingFile.start_position,
                            TaskForProcessingFile.max_offset])\
        .from_(TaskForProcessingFile)\
        .join(FileForProcessing, JOIN.LEFT_OUTER, on=(TaskForProcessingFile.file == FileForProcessing.id))\
        .where(FileForProcessing.date_lost.is_null(True))

    selection = query.execute(core_db)

    for part_file in selection:
        print(part_file)


def add_monitoring_point():
    new_monitoring_point = MonitoringPoint()
    new_monitoring_point.description = 'логи тех. журнала 1с'
    new_monitoring_point.monitoring = True
    new_monitoring_point.settings = '{"PATH":"E:/1cTJ/",' \
                                    '"DEEP":-1,' \
                                    '"FILTER":"[0-9]{8}.log"}'
    new_monitoring_point.save()


if __name__ == '__main__':
    inspect_folders()
