from functools import cache
from pymongo import MongoClient


@cache
def get_db(url='mongodb://127.0.0.1:27017/', dbname='aol_calendar'):
    client = MongoClient(url)
    return client[dbname]
