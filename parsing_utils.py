from datetime import date
import re


COURSE_NAME_TYPE = {
    'art excel': 'art_excel',
    'dsn': 'dsn',
    'дсн': 'dsn',
    'yes!': 'yes',
    'yes+': 'yes',
    'блессинг': 'blessing',
    'глубокий сон и снятие тревожности': 'deep_sleep',
    'забота о спине и коррекция осанки': 'spine_care',
    'здоровое питание': 'cooking',
    'искусство медитации': 'art_of_meditation',
    'искусство тишины online': 'art_of_silence',
    'искусство тишины интенсив': 'art_of_silence',
    'искусство тишины': 'art_of_silence',
    'йога для позвоночника': 'yoga',
    'йога': 'yoga',
    'первый шаг': 'first_step',
    'песенный сатсанг': 'satsang',  # 🎸
    'победи зависимость': 'give_up_smoking',
    'поддерживающее занятие online': 'practices',
    'поддерживающее занятие для vtp': 'practices',
    'поддерживающее занятие': 'practices',
    'процесс вечности': 'eternity',
    'процесс интуиции 5-8 лет': 'intuition',
    'процесс интуиции 8-18 лет': 'intuition',
    'процесс интуиции': 'intuition',
    'саньям': 'sanyam',
    'суставная йога': 'yoga',
    'счастье (благотворительный)': 'happiness',
    'счастье': 'happiness',
    'счастье онлайн': 'happiness_online',
    'шри шри йога 2': 'ssy2',
    'шри шри йога': 'ssy',
}


def get_course_type(name, default='unknown'):
    """Возвращает тип курса по имени

    Используется при парсинге дата-файлов (JSON-файлов)/данных из админки
    """
    return COURSE_NAME_TYPE.get(name.lower(), default)


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

    # Словарик для перевода названий месяцев
    month_map = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }

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
        month1 = month_map[month1_str.lower()]
        month2 = month_map[month2_str.lower()]

        date1 = date(year, month1, int(day1_str))
        date2 = date(year, month2, int(day2_str))
        return [date1, date2]

    elif match_month_range:
        day1_str, day2_str, month_str = match_month_range.groups()
        month = month_map[month_str.lower()]

        date1 = date(year, month, int(day1_str))
        date2 = date(year, month, int(day2_str))
        return [date1, date2]

    elif match_single_date:
        day_str, month_str = match_single_date.groups()
        month = month_map[month_str.lower()]

        single_date = date(year, month, int(day_str))
        return [single_date]

    else:
        raise ValueError(f"Неизвестный формат строки: '{date_str}'")
