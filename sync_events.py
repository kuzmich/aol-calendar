"""Получает курсы из админки и объединяет их с курсами в базе.

Нужно время от времени получать курсы их админки, чтобы данные в календаре были
актуальными.  При этом у нас есть 2 типа курсов в базе: полученные из админки и введенные
через форму. Также курсы из админки могут быть скорректированы через форму. Т.е. нельзя
просто взять и удалить все админские курсы из базы и получить их заново - их нужно
объединять.
"""
from db_utils import get_db


def update_type(col, name, new_type):
    result = col.update_many({'name': name}, {'$set': {'type': new_type}})
    return result


def make_event_types_unique():
    """Делает так, чтобы у все событий был свой уникальный тип курса

    Например, есть 3 курса интуиции: Процесс интуиции, Процесс интуиции 5-8 лет и Процесс
    интуиции 8-18 лет. У них у всех тип курса intuition. Функция исправит типы на
    intuition, intuition_5_8, intuition_8_18.
    """
    db = get_db()
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


def get_public_link(event_type, event_id):
    public_link = 'https://artofliving.ru/{event_path}?streamId={event_id}#offerBlock'

    EVENT_TYPE_PATH = {
        'art_excel': "artexcel",
        'dsn': "dns",
        'yes': "yes",
        'yes_plus': "yesplus",
        'blessing': "blessing",
        'deep_sleep': "deep-sleep",
        'cooking': "cookie",
        'premium': "premium",
        'meditation': "meditation",
        'silence': "art-of-silence",
        'silence_online': "art-of-silence_online",
        'first_step': "firststep",
        'give_up_smoking': "give-up-smoking",
        'intuition_5_8': "intuition-process-5-7",
        'intuition_8_18': "intuition-process-8-18",
        'sanyam': 'sanyam',
        'happiness': "happiness",
        'ssy': "yoga",
        'ssy2': "srisriyoga2",
        'practices_online': "practice-online",
        # '': "",
        # '': "",
        # '': "",
        # '': "",
        # '': "",
        # '': "",
    }

    if event_type in EVENT_TYPE_PATH:
        return public_link.format(event_path=EVENT_TYPE_PATH[event_type],
                                  event_id=event_id)


def add_public_link():
    db = get_db()
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
    # make_event_types_unique()
    add_public_link()
