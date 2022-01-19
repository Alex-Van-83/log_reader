from os import path, mkdir
from peewee import SqliteDatabase

core = None


def create_core(directory, db_name):

    if not path.isdir(directory):
        mkdir(directory)
    return SqliteDatabase(f'{directory}/{db_name}')
