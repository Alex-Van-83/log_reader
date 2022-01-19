import time
import schedule
from db_model import *


def inspect_folders():

    with core:
        points = MonitoringPoint.select().where(MonitoringPoint.monitoring == True)
        for point in points:
            print(point.settings)


def create_task_list():
    schedule.every(1).minute.do(inspect_folders)


def main():
    create_task_list()
    while True:
        schedule.run_pending()
        time.sleep(1)


def init_db():
    create_tables_model(core)


if __name__ == '__main__':
    init_db()
    # main()
    inspect_folders()
