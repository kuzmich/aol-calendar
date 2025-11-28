from datetime import datetime
from functools import cache, lru_cache
import json
from pathlib import Path

from bson.objectid import ObjectId
from pymongo import MongoClient

from .cal import next_month_first_day


# TODO Вынести настройки в конфиг
@cache
def get_db(url='mongodb://127.0.0.1:27017/', dbname='aol_calendar'):
    client = MongoClient(url)
    return client[dbname]


def add_events(events):
    db = get_db()
    col = db['events']

    for e in events:
        col.insert_one(e)


def get_events(year, month):
    """Получаем события из базы за последний месяц"""
    db = get_db()
    col = db['events']
    start_of_month = datetime(year, month, 1)
    cursor = col.find(
        {'start_date': {'$gte': start_of_month,
                        '$lt': next_month_first_day(start_of_month)}}
    )
    return [e for e in cursor]


def get_event_by_id(event_id):
    db = get_db()
    col = db['events']
    return col.find_one({'_id': ObjectId(event_id)})


def save_event(event_id, event):
    db = get_db()
    col = db['events']

    col.replace_one(
        {'_id': ObjectId(event_id)},
        event
    )


def delete_event(event_id):
    db = get_db()
    col = db['events']
    col.delete_one({'_id': ObjectId(event_id)})


@lru_cache(maxsize=1)
def get_all_event_names_types():
    db = get_db()
    events_col = db['events']
    name_type_list = [(event['type'], event['name']) for event in events_col.find({}, {'name': 1, 'type': 1})]
    return sorted(set(name_type_list), key=lambda nt: nt[1])


@lru_cache(maxsize=1)
def get_all_teachers():
    db = get_db()
    events_col = db['events']
    list_of_list_of_teachers = (event.get('teachers', []) for event in events_col.find({}, {'teachers': 1}))
    teachers = (teacher for list_of_teachers in list_of_list_of_teachers for teacher in list_of_teachers)
    return sorted(set(teachers))


@lru_cache(maxsize=1)
def get_all_locations():
    db = get_db()
    events_col = db['events']
    return sorted(
        set(event['place'] for event in events_col.find({}, {'place': 1})),
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
