import os
import json
from db_model import *


def take_files(file_path, deep, mask, new_files, files_for_processing):
    for fs_object in os.listdir(file_path):
        new_path = os.path.join(file_path, fs_object)
        if os.path.isdir(new_path) and deep:
            take_files(new_path, deep-1, mask, new_files, files_for_processing)
        elif os.path.isfile(new_path):
            if fs_object.find(mask):
                file_info = os.stat(new_path)
                if new_path in files_for_processing:
                    FileForProcessing.update(size=round(file_info.st_size / 1024)) \
                                     .where(
                                            FileForProcessing.full_path == new_path
                                        ) \
                                    .execute()

                    files_for_processing.remove(new_path)
                else:
                    new_files.append({'full_path': new_path,
                                      'size': round(file_info.st_size / 1024),
                                      'description': str(fs_object),
                                      'directory': os.path.split(file_path)[-1]
                                      })


def inspect_folders():

    with core_db:
        points = MonitoringPoint.select(
                                        MonitoringPoint.id,
                                        MonitoringPoint.settings
                                        )\
                                .where(
                                        MonitoringPoint.monitoring == True
                                      )
        for point in points:
            settings = json.loads(point.settings)
            files_for_processing = FileForProcessing.select(
                FileForProcessing.full_path
            ).where(
                (FileForProcessing.timestamp_lost == FileForProcessing.timestamp_created) # not losted
                &
                ((FileForProcessing.timestamp_scheduled == FileForProcessing.timestamp_created) # not scheduled
                    |
                 (FileForProcessing.timestamp_processed == FileForProcessing.timestamp_created)) # not processed
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
