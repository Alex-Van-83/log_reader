import schedule
from time import sleep
from inspector_folders import inspect_folders, create_task_for_read_file
from db_model import init_db


def create_task_list():
    schedule.every(1).minute.do(inspect_folders)
    schedule.every(1).minute.do(create_task_for_read_file)


def main():
    create_task_list()
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    init_db()
    main()
