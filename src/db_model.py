from peewee import *
from db_library import *
from datetime import datetime
from time import time as timestamp


class Base(Model):
    id = PrimaryKeyField(unique=True, index=True)
    description = CharField(255)
    timestamp_created = TimestampField(default=timestamp)
    date_created = DateTimeField(default=datetime.now)

    class Meta:
        database = core_db


class MonitoringPoint(Base):
    points_type = CharField(32, default='FILE_DIRECTORY')
    monitoring = BooleanField(index=True, default=False)
    settings = TextField(default='')

    class Meta:
        db_table = 'MonitoringPoints'


class FileForProcessing(Base):

    basic_directory = ForeignKeyField(MonitoringPoint, null=False)
    directory = CharField(255)
    full_path = CharField()
    size = IntegerField(null=True)

    timestamp_scheduled = TimestampField(null=True)
    date_scheduled = DateTimeField(null=True)

    timestamp_processed = TimestampField(null=True)
    date_processed = DateTimeField(null=True)

    timestamp_lost = TimestampField(null=True)
    date_lost = DateTimeField(null=True)

    class Meta:
        db_table = 'FilesForProcessing'
        indexes = (
                (('date_lost', 'date_scheduled', 'date_processed', 'date_created', 'id'), True),
                )


def create_tables_model(db):
    db.create_tables([MonitoringPoint, FileForProcessing])


def init_db():
    create_tables_model(core_db)
