"""Получает курсы из админки и объединяет их с курсами в базе"""
import argparse
import logging

from aol_calendar.utils import get_config
from aol_calendar.utils.db import get_db, set_db_var, add_events, save_event
from aol_calendar.utils.admin import AdminCourses
from aol_calendar.utils.parsing import parse_admin_event


logger = logging.getLogger('sync_events')


def merge_admin_event(db_event, admin_event):
    de, ae = db_event, admin_event
    logger.debug(f'Merging event id {de["_id"]} {de["name"]} ({de["dates"]}, {de["place"]})')

    common_keys = set(ae.keys()).intersection(de.keys())
    for key in common_keys:
        if ae[key] != de[key]:
            # даты могут отличаться тире: '28–30 ноября' и '28-30 ноября' (admin, db)
            if key == 'dates' and len(ae[key]) == len(de[key]):
                continue
            logger.debug(f'Updating {key}: {de[key]} => {ae[key]}')
            de[key] = ae[key]

    admin_only_keys = set(ae.keys()).difference(de.keys())
    for key in admin_only_keys:
        logger.debug(f'Setting {key} = {ae[key]}')
        de[key] = ae[key]

    db_only_keys = set(de.keys()).difference(ae.keys())
    # _id и public_link есть только в базе
    db_only_keys = db_only_keys.difference({'_id'})  # , 'public_link'
    if db_only_keys:
        logger.debug('DB only values: %s', ', '.join(f'{key}: {de[key]}' for key in db_only_keys))

    return db_event


def parse_args():
    parser = argparse.ArgumentParser(
        description='Получает данные о курсах из админки и объединяет их с данными в базе'
    )
    parser.add_argument('year', type=int)
    parser.add_argument('month', type=int)
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    logging.getLogger('pymongo').setLevel('INFO')
    logging.getLogger('urllib3').setLevel('INFO')

    args = parse_args()

    config = get_config()
    email = config.EMAIL
    password = config.PASSWORD

    db = get_db(config.DB_URL, config.DB_NAME)
    set_db_var(db)

    year = args.year
    month = args.month

    adm = AdminCourses((email, password))
    courses = adm.get_courses(year, month, include_free=True)
    events = list(map(lambda c: parse_admin_event(c, year), courses))
    events = [e for e in events if not (e.get('status') == 'Не опубликован' and e.get('num_payments') == 0)]

    col = db['events']

    for event in events:
        db_event = col.find_one(
            {'type': event['type'],
             'start_date': event['start_date'],
             'end_date': event['end_date']}
        )

        if not db_event and 'admin_id' in event:
            db_event = col.find_one({'admin_id': event['admin_id']})
            if db_event:
                logger.debug('Event %s found by admin_id %s', event['name'], event['admin_id'])

        if not db_event:
            logger.debug('Inserting new event: %s', f"{event['name']} | {event['dates']} | {event['place']}")
            add_events([event])
        else:
            db_event = merge_admin_event(db_event, event)
            save_event(str(db_event['_id']), db_event)
