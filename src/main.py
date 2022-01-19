import time
import schedule

db = None

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

    import db_library
    db_library.core = db_library.create_core('../db', 'reader.db')

    import db_model as m
    m.create_tables_model(db_library.core)





