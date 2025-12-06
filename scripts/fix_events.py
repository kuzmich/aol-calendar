from aol_calendar.utils import get_config
from aol_calendar.utils.db import get_db, set_db_var, mongo_db
from aol_calendar.utils.parsing import get_public_link


def update_type(col, name, new_type):
    result = col.update_many({'name': name}, {'$set': {'type': new_type}})
    return result


def make_event_types_unique():
    """Делает так, чтобы у все событий был свой уникальный тип курса

    Например, есть 3 курса интуиции: Процесс интуиции, Процесс интуиции 5-8 лет и Процесс
    интуиции 8-18 лет. У них у всех тип курса intuition. Функция исправит типы на
    intuition, intuition_5_8, intuition_8_18.
    """
    db = mongo_db
    col = db['events']

    rename_pairs = [
        ('YES+', 'yes_plus'),
        ('Искусство тишины', 'silence'),
        ('Искусство тишины online', 'silence_online'),
        ('Искусство медитации', 'meditation'),
        ('Йога для позвоночника', 'yoga_spine'),
        ('Поддерживающее занятие online', 'practices_online'),
        ('Поддерживающее занятие для VTP', 'practices_vtp'),
        ('Процесс интуиции 5-8 лет', 'intuition_5_8'),
        ('Процесс интуиции 8-18 лет', 'intuition_8_18'),
        ('Суставная йога', 'yoga_joints'),
    ]
    results = [update_type(col, name, new_type) for name, new_type in rename_pairs]
    for rn_pair, res in zip(rename_pairs, results):
        print(f'{rn_pair[0]}: {res.matched_count}/{res.modified_count} (matched/modified)')


def add_public_link():
    db = mongo_db
    col = db['events']

    for event in col.find({'admin_link': {'$exists': True}}):
        public_link = get_public_link(event['type'], event['admin_id'])
        if not public_link:
            print(event['type'])
        else:
            result = col.update_one(
                {'_id': event['_id']},
                {'$set': {'public_link': public_link}}
            )
            if result.modified_count != 1:
                print(result, event['_id'])


if __name__ == '__main__':
    config = get_config()
    set_db_var(get_db(config.DB_URL, config.DB_NAME))

    # make_event_types_unique()
    add_public_link()
