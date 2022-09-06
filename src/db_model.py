from peewee import *
from db_library import *
from datetime import datetime
from time import time as timestamp


class Base(Model):
    id = PrimaryKeyField(unique=True, index=True)
    timestamp_created = TimestampField(default=timestamp)
    date_created = DateTimeField(default=datetime.now)

    class Meta:
        database = core_db


class MonitoringPoint(Base):

    description = CharField(255)
    points_type = CharField(32, default='FILE_DIRECTORY')
    monitoring = BooleanField(index=True, default=False)
    settings = TextField(default='')

    class Meta:
        db_table = 'MonitoringPoints'


class FileForProcessing(Base):

    monitoring_point = ForeignKeyField(MonitoringPoint, null=False)
    full_path = CharField()
    directory = CharField(255)
    file_name = CharField(255)
    size = IntegerField(null=True)
    last_position = IntegerField()
    completed = BooleanField()

    timestamp_lost = TimestampField(null=True)
    date_lost = DateTimeField(null=True)

    class Meta:
        db_table = 'FilesForProcessing'
        indexes = (
                (('date_lost', 'id'), True),
                )


class TaskForProcessingFile(Base):

    file = ForeignKeyField(FileForProcessing, null=False)
    start_position = IntegerField(null=False, default=0)
    max_offset = IntegerField(null=False, default=0)

    class Meta:
        db_table = 'TasksForProcessingFile'


class StartPointReadPartFile(Base):

    file = ForeignKeyField(FileForProcessing, null=False)
    task = ForeignKeyField(TaskForProcessingFile, null=False)
    start_position = IntegerField(null=False, default=0)
    executor = IntegerField(null=False)

    class Meta:
        db_table = 'StartPoints'


class ReadPartFile(Base):

    file = ForeignKeyField(FileForProcessing, null=False)
    task = ForeignKeyField(TaskForProcessingFile, null=False)
    start_position = IntegerField(null=False, default=0)
    end_position = IntegerField(null=False, default=0)
    executor = IntegerField(null=False)
    row_count = IntegerField(null=False, default=0)
    event_count = IntegerField(null=False, default=0)
    duration = IntegerField(null=False, default=0)

    class Meta:
        db_table = 'ReadPartsFile'
#
#
# class ProcessedPartFile(Base):
#
#     file = ForeignKeyField(FileForProcessing, null=False)
#     task = ForeignKeyField(TaskForProcessingFile, null=False)
#     reader = ForeignKeyField(ReadPartFile, null=False)
#     executor = IntegerField(null=False)
#     event_count = IntegerField(null=False, default=0)
#     duration = IntegerField(null=False, default=0)
#
#     class Meta:
#         db_table = 'ProcessedReadPartsFile'



def create_tables_model(db):
    db.create_tables([MonitoringPoint, FileForProcessing, TaskForProcessingFile, ReadPartFile])#, ProcessedPartFile


def init_db():
    create_tables_model(core_db)


if __name__ == '__main__':
    init_db()
