from datetime import datetime, date
import logging
import re

from ..const import Month, COURSE_NAME_TYPE, EVENT_TYPE_PATH, PUBLIC_LINK_TEMPLATE


logger = logging.getLogger(__name__)


def get_course_type(name, default='unknown'):
    """Возвращает тип курса по имени

    Используется при парсинге данных из админки и дата-файлов (JSON-файлов)

    >>> get_course_type('Счастье')
    happiness
    """
    course_type = COURSE_NAME_TYPE.get(name.lower(), None)

    if course_type is None:
        logger.warning("Can't parse event name '%s'", name)
        return default
    else:
        return course_type


def parse_dates(date_str, year):
    """
    Парсит строку в одну или две даты в зависимости от формата.

    Args:
        date_str (str): Строка с датой или диапазоном дат.
        Примеры: '31 Октября-2 Ноября', '17-19 Октября', '19 Октября'.

    Returns:
        list: Список объектов datetime.date.
        Например: [datetime.date(2025, 10, 31), datetime.date(2025, 11, 2)]
    """

    # Регулярные выражения для разных форматов
    # 1. '31 Октября-2 Ноября'
    pattern_full_range = r'(\d+)\s+([А-Яа-я]+)[-–](\d+)\s+([А-Яа-я]+)'
    # 2. '17-19 Октября'
    pattern_month_range = r'(\d+)[-–](\d+)\s+([А-Яа-я]+)'
    # 3. '19 Октября'
    pattern_single_date = r'(\d+)\s+([А-Яа-я]+)'

    # Попытка найти совпадение по регулярным выражениям
    match_full_range = re.match(pattern_full_range, date_str, re.IGNORECASE)
    match_month_range = re.match(pattern_month_range, date_str, re.IGNORECASE)
    match_single_date = re.match(pattern_single_date, date_str, re.IGNORECASE)

    # Обработка совпадений
    if match_full_range:
        day1_str, month1_str, day2_str, month2_str = match_full_range.groups()
        month1 = Month[month1_str.lower()].value
        month2 = Month[month2_str.lower()].value

        date1 = date(year, month1, int(day1_str))
        date2 = date(year, month2, int(day2_str))
        return [date1, date2]

    elif match_month_range:
        day1_str, day2_str, month_str = match_month_range.groups()
        month = Month[month_str.lower()].value

        date1 = date(year, month, int(day1_str))
        date2 = date(year, month, int(day2_str))
        return [date1, date2]

    elif match_single_date:
        day_str, month_str = match_single_date.groups()
        month = Month[month_str.lower()].value

        single_date = date(year, month, int(day_str))
        return [single_date]

    else:
        raise ValueError(f"Неизвестный формат строки: '{date_str}'")


def parse_admin_event(admin_event, year):
    dates = parse_dates(admin_event['date'], year)

    # вот возможные ключи у события из дата-файлов
    # {'name', 'date', 'place', 'year', 'month', 'time', 'teachers', 'link', 'id', 'status', 'num_payments'}
    event = {
        'name': admin_event['name'],
        'dates': admin_event['date'].lower(),
        'place': admin_event['place'],
        'type': get_course_type(admin_event['name']),
        'start_date': datetime.combine(dates[0], datetime.min.time()),
        'end_date': datetime.combine(dates[-1], datetime.min.time()),
    }

    if admin_event.get('teachers'):
        teachers = [t.strip() for t in admin_event['teachers'].split(',')]
        teachers = [swap_names(t) if t not in ['Коробко Анастасия', 'Кашикар Динеш'] else t for t in teachers]
        event['teachers'] = teachers

    if 'time' in admin_event:
        event['time'] = admin_event['time']

    if 'num_payments' in admin_event:
        event['num_payments'] = admin_event['num_payments']

    if 'status' in admin_event:
        event['status'] = admin_event['status']

    if 'link' in admin_event:
        event['admin_link'] = admin_event['link']
        event['admin_id'] = admin_event['id']

        if (public_link := get_public_link(event['type'], event['admin_id'])):
            event['public_link'] = public_link

    return event


def swap_names(name):
    """Меняет 'имя фамилия' на 'фамилия имя' или наоборот"""
    name_parts = name.split()
    if len(name_parts) == 2:
        first, last = name_parts
        return f'{last} {first}'
    return name


def get_public_link(event_type, event_id):
    """Возвращает публичную ссылку на событие на сайте artofliving.ru"""
    if event_type in EVENT_TYPE_PATH:
        return PUBLIC_LINK_TEMPLATE.format(event_path=EVENT_TYPE_PATH[event_type],
                                           event_id=event_id)
    else:
        logger.warning("Can't make public_link for event type %s and admin_id %s",
                       event_type, event_id)

