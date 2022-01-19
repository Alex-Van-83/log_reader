from peewee import *
import db_library
from datetime import datetime
from time import time as timestamp


class Base(Model):
    id = PrimaryKeyField(unique=True, index=True)
    description = CharField(255)
    timestamp_creation = TimestampField(default=timestamp)
    date_creation = DateTimeField(default=datetime.now)

    class Meta:
        database = db_library.core


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
    size = IntegerField()

    timestamp_scheduled = TimestampField()
    date_scheduled = DateTimeField()

    timestamp_processed = TimestampField()
    date_processed = DateTimeField()

    timestamp_lost = TimestampField()
    date_lost = DateTimeField()

    class Meta:
        db_table = 'FilesForProcessing'
        indexes = (
                (('timestamp_lost', 'timestamp_scheduled', 'timestamp_processed', 'id'), True),
                )


def create_tables_model(db):
    db.create_tables([MonitoringPoint, FileForProcessing])
