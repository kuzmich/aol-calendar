from datetime import datetime
from functools import cache, lru_cache
import json
from pathlib import Path

from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.database import Database

from .cal import next_month_first_day


mongo_db: Database


@cache
def get_db(url, dbname):
    client = MongoClient(url)
    return client[dbname]


def set_db_var(db):
    global mongo_db
    mongo_db = db


def add_events(events):
    col = mongo_db['events']

    for e in events:
        col.insert_one(e)


def get_events(year, month):
    """Получаем события из базы за последний месяц"""
    col = mongo_db['events']
    start_of_month = datetime(year, month, 1)
    cursor = col.find(
        {'start_date': {'$gte': start_of_month,
                        '$lt': next_month_first_day(start_of_month)}}
    )
    return [e for e in cursor]


def get_event_by_id(event_id):
    col = mongo_db['events']
    return col.find_one({'_id': ObjectId(event_id)})


def save_event(event_id, event):
    col = mongo_db['events']

    col.replace_one(
        {'_id': ObjectId(event_id)},
        event
    )


def delete_event(event_id):
    col = mongo_db['events']
    col.delete_one({'_id': ObjectId(event_id)})


@lru_cache(maxsize=1)
def get_all_event_names_types():
    col = mongo_db['events']
    name_type_list = [(event['type'], event['name']) for event in col.find({}, {'name': 1, 'type': 1})]
    return sorted(set(name_type_list), key=lambda nt: nt[1])


@lru_cache(maxsize=1)
def get_all_teachers():
    col = mongo_db['events']
    list_of_list_of_teachers = (event.get('teachers', []) for event in col.find({}, {'teachers': 1}))
    teachers = (teacher for list_of_teachers in list_of_list_of_teachers for teacher in list_of_teachers)
    return sorted(set(teachers))


@lru_cache(maxsize=1)
def get_all_locations():
    col = mongo_db['events']
    return sorted(
        set(event['place'] for event in col.find({}, {'place': 1})),
        key=lambda pl: pl.lower()
    )


def get_manual_entries(data_file, default=[]):
    data_file = Path(data_file)
    entries = default
    if data_file.exists():
        with data_file.open() as f:
            entries = json.load(f)
    return entries


def sort_locations(location):
    return location.lower()


def sort_events(type_name):
    return type_name[1]
