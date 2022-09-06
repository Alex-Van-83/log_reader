import schedule
import loger
from time import sleep
from datetime import datetime
from inspector_folders import inspect_folders, create_task_for_read_file, start_read_file_by_task
from db_model import init_db


def create_task_list():
    schedule.every(1).minute.do(inspect_folders)
    schedule.every(1).minute.do(create_task_for_read_file)
    schedule.every(1).minute.do(start_read_file_by_task)


def main():
    create_task_list()
    while True:
        loger.write_log('main', f'main: start {datetime.now()}\n')
        schedule.run_pending()
        loger.write_log('main', f'main: end {datetime.now()}\n')
        sleep(1)


if __name__ == '__main__':
    init_db()
    main()
