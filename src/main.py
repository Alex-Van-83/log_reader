import time
import schedule


def inspect_folders():
    pass


def create_task_list():
    schedule.every(5).seconds.do(inspect_folders)


def main():
    create_task_list()
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()