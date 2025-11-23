from functools import cache, lru_cache
from pymongo import MongoClient


@cache
def get_db(url='mongodb://127.0.0.1:27017/', dbname='aol_calendar'):
    client = MongoClient(url)
    return client[dbname]


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
