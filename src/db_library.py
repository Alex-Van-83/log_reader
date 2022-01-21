from os import path, mkdir
from peewee import SqliteDatabase


directory = '../db'
db_name = 'reader.db'

if not path.isdir(directory):
    mkdir(directory)

core_db = SqliteDatabase(f'{directory}/{db_name}')
