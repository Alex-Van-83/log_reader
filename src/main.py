import schedule
from time import sleep
from inspector_folders import inspect_folders
from db_model import init_db


def create_task_list():
    schedule.every(1).minute.do(inspect_folders)


def main():
    create_task_list()
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    init_db()
    main()
