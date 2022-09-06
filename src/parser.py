import multiprocessing as mp
import datetime
import re
import time
import hashlib
import os


def flash_cash(cash, events_array):
    if len(cash):
        events_array.append(''.join(cash))
        cash.clear()


def flash_events_array(events_array, event_regexp_properties):
    list_properties_for_hash = ('Sql', 'planSQLText', 'Context', 'Sdbl')
    event_regexp_time_duration_name = re.compile(r'([0-9]{2}):([0-9]{2}).([0-9]+)-([0-9]+),([a-zA-z]+),([0-9]+),(.*)')
    hash_maker = hashlib.sha1()

    event_count = 0
    start = time.perf_counter()
    time_start = datetime.datetime.now()
    for event_text in events_array:
        event_count += 1
        description_event = event_regexp_time_duration_name.findall(event_text)
        new_event = dict(zip(['minute', 'second', 'moment', 'duration', 'event', 'stek'], description_event[0]))

        for event_regexp in event_regexp_properties:
            take_properties(new_event, event_regexp.findall(description_event[0][6]))

        for name_properties in list_properties_for_hash:
            if name_properties in new_event.keys():
                hash_maker.update(new_event[name_properties].encode(encoding="utf-8"))
                new_event[name_properties] = hash_maker.hexdigest()
        write_debug(new_event)

    report_text = f'\rСобытий {event_count}  секунд {time.perf_counter() - start :0.4f} {time_start} - '

    write_log(report_text)

    events_array.clear()


def take_properties(event, properties_list):
    for name_value in properties_list:
        if type(name_value) == str:
            properties = name_value.split('=', 1)
        else:
            properties = name_value[0].split('=', 1)

        event[properties[0]] = properties[1]


def write_log(report_text):
    log = open('../file/log.txt', 'a', encoding="utf-8")
    log.write(f'{report_text} {datetime.datetime.now()} {os.getpid()} /n')
    log.close()


def write_debug(report_text):
    if 0:
        log = open(f'../debug/{os.getpid()}_debug.txt', 'a', encoding="utf-8")
        log.write(f'{report_text} {os.getpid()}\n')
        log.close()


def run_new_process(process_array, limit_runing_process, events_array, event_regexp_properties):
    if len(process_array) >= limit_runing_process:
        task = process_array.pop()
        task.join()

    event_processor = mp.Process(target=flash_events_array, args=(events_array, event_regexp_properties))
    event_processor.daemon = True
    event_processor.start()
    process_array.append(event_processor)


def append_event(cash, limit_events_array, events_array, process_array, event_regexp_properties, limit_runing_process):
    flash_cash(cash, events_array)
    processing_time_start = time.perf_counter()
    if len(events_array) >= limit_events_array:
        run_new_process(process_array, limit_runing_process, events_array, event_regexp_properties)
        events_array.clear()
    return time.perf_counter() - processing_time_start


def take_event_from_file(filename):

    cash = []
    events_array = []

    process_array = []

    event_count = 0
    row_count = 0
    processing_time_total = 0

    event_regexp_begin = re.compile(r'^[0-9]{2}:[0-9]{2}.[0-9]+-[0-9]+')
    event_patern_properties = [r':(\w+=[\w|-]+[^,]*)', r',(\w+=[\w|-]+[^,]*)', r',(\w+=([^\w,-]).*?\2)']
    event_regexp_properties = [re.compile(event_patern) for event_patern in event_patern_properties]

    limit_events_array = 50000
    limit_runing_process = 3
    start = time.perf_counter()
    time_start = datetime.datetime.now()

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            row_count += 1
            if event_regexp_begin.match(line):
                event_count += 1
                processing_time_total += append_event(cash, limit_events_array, events_array,
                                                      process_array, event_regexp_properties, limit_runing_process)
                cash.append(line.rstrip())
            else:
                cash.append(line.rstrip())

    processing_time_total += append_event(cash, 0, events_array,
                                          process_array, event_regexp_properties, limit_runing_process)

    finish = time.perf_counter()

    report_text = f'\rСобытий {event_count} строк {row_count} секунд {finish - start :0.4f} ' \
                  f'({processing_time_total:0.4f}) {time_start} - '
    write_log(report_text)

    for job in process_array:
        job.join()


if __name__ == '__main__':
    print(datetime.datetime.now())
    take_event_from_file('../file/19092321.log')
    # take_event_from_file('../file/19111813.log')
    print(datetime.datetime.now())
