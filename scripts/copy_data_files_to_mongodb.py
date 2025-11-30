import json
from pathlib import Path
from pprint import pprint
import re

from pymongo import MongoClient

from aol_calendar.utils.parsing import parse_admin_event, swap_names


data_file_name_re = re.compile(r'\d{4}_\d{1,2}.json')


def get_db(url='mongodb://127.0.0.1:27017/', dbname='aol_calendar'):
    client = MongoClient(url)
    return client[dbname]


def year_month(data_file):
    """Возвращает пару (год, месяц)"""
    return tuple(map(int, data_file.stem.split('_')))


def get_data_files(data_dir):
    """Возвращает все пути к дата-файлам из папки data_dir"""

    data_files = data_dir.glob('*.json')
    data_files = filter(lambda p: data_file_name_re.match(p.name), data_files)
    sorted_files = sorted(data_files, key=year_month)
    return sorted_files


def get_json_data(data_file):
    with data_file.open() as f:
        return json.load(f)


def get_month_data(data_file):
    """Читает данные из дата-файла админки и дополняет информацией из файла ручного ввода

    Возвращает ((год, месяц), [все события за выбранный месяц])
    """
    month_data = get_json_data(data_file)

    if (manual_file := (data_file.parent / 'manual' / data_file.name)).exists():
        month_data.extend(get_json_data(manual_file))

    return (year_month(data_file), month_data)


def get_events(data_dir):
    """Возвращает список событий из папки с дата-файлами"""

    # получам список файлов [Path('data/2026_1.json'), ...]
    data_files = get_data_files(data_dir)

    # получаем данные из дата-файлов [((year, month), month_data), ...]
    month_data = list((year_month(df), get_json_data(df)) for df in data_files)

    # разворачиваем в плоский список событий и дописываем год и месяц
    return [event | {'year': ym[0], 'month': ym[1]} for ym, md in month_data for event in md]


def get_all_events(data_dir):
    """Возвращает объединенный список событий из обоих папок с дата-файлами"""

    # получам список файлов [Path('data/2026_1.json'), ...]
    data_files = get_data_files(data_dir)

    # получаем данные из дата-файлов [((year, month), month_data), ...]
    month_data = list(get_month_data(df) for df in data_files)

    # разворачиваем в плоский список событий и дописываем год и месяц
    return [event | {'year': ym[0], 'month': ym[1]} for ym, md in month_data for event in md]


def find_event(events, key=None, value=None, test_func=None):
    """Находит событие либо просто по значению ключа, любо по другой логике в test_func

    Примеры:
        find_event(month_data, 'name', 'Счастье (благотворительный)')
        find_event(month_data, 'place', 'online')
        find_event(month_data, test_func=lambda e: e['name'] == 'Процесс интуиции' and e.get('status') != 'Не опубликован')
    """
    for event in events:
        if test_func:
            if test_func(event):
                yield event
        else:
            if event[key] == value:
                yield event


def get_teacher_ids(e, teacher_name_id):
    ids = []
    for full_name in e.get('teachers', '').split(', '):
        if not full_name:
            continue
        if full_name in teacher_name_id:
            ids.append(teacher_name_id[full_name])
        elif (swapped_full_name := swap_names(full_name)) in teacher_name_id:
            ids.append(teacher_name_id[swapped_full_name])
        else:
            raise Exception(f'Unknown teacher {full_name}')
    return ids


def get_all_locations(events):
    return sorted(set(event['place'] for event in events))


def get_all_event_names(events):
    names = sorted(set(event['name'] for event in events))
    # names.remove('Счастье (благотворительный)')  # это все равно обычное Счастье
    return names


def get_all_teachers(events):
    """Возвращает список всех учителей, фигурировавших в событиях"""

    list_of_list_of_teachers = (event.get('teachers', '').split(', ') for event in events)
    teachers = (teacher for list_of_teachers in list_of_list_of_teachers for teacher in list_of_teachers)
    swapped_names = (swap_names(t) for t in set(teachers))
    non_empty_names = (n for n in swapped_names if n)
    sorted_names = sorted(non_empty_names, key=lambda n: n[0])
    return sorted_names


if __name__ == '__main__':
    db = get_db()
    events_col = db['events']
    data_dir = Path('data')

    events = get_all_events(data_dir)
    # отфильтровываем отмененные курсы
    events = [e for e in events if not (e.get('status') == 'Не опубликован' and e.get('num_payments') == 0)]

    # Сохраним учителей, названия событий и мест в отдельные коллекции

    # teachers_col = db['teachers']
    # event_types = db['event_types']
    # locations_col = db['locations']

    # записываем названия курсов
    # names = get_all_event_names(events)
    # event_types.insert_many([{'name': name} for name in names])

    # записываем местоположения курсов
    # locations = get_all_locations(events)
    # locations_col.insert_many([{'name': loc} for loc in locations])

    # записываем учителей
    # all_teachers = get_all_teachers(events)
    # teachers_col.insert_many([{'first_name': n[1], 'last_name': n[0]} for n in all_teachers])

    # получаем идентификаторы записей для типов событий, местоположений и учителей
    # event_name_id = {e['name']: e['_id'] for e in event_types.find()}
    # location_name_id = {l['name']: l['_id'] for l in locations_col.find()}
    # teacher_name_id = {f"{t['first_name']} {t['last_name']}": t['_id'] for t in teachers_col.find()}

    counter = 0
    for e in events:
        event = parse_admin_event(e, e['year'])
        events_col.insert_one(event)
        counter += 1
        # pprint(event, sort_dicts=False)

    print(f'Скопировано {counter} событий')
