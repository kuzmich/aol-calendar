"""Разные утилиты для работы с календарем"""
import calendar
from datetime import datetime, date, timedelta
from itertools import groupby


def next_month_first_day(d):
    """Возвращает первый день следующего месяца"""

    _, last_day = calendar.monthrange(d.year, d.month)
    # Переходим на последний день текущего месяца и добавляем 1 день
    return datetime(d.year, d.month, last_day) + timedelta(days=1)


def weekdays_in_month(year: int, month: int, weekday: int):
    """Возвращает все даты определенного дня недели в месяце

    Например, все среды в апреле 2026:

    >>> weekdays_in_month(2026, 4, calendar.WEDNESDAY)
    [date(2026, 4, 1), date(2026, 4, 8), date(2026, 4, 15), date(2026, 4, 22), date(2026, 4, 29)]
    """
    cal = calendar.Calendar()
    return [
        date(year, month, day)
        for week in cal.monthdayscalendar(year, month)
        for day in [week[weekday]]
        if day != 0
    ]


def get_month_dates(year, month):
    """Возвращает даты текущего месяца, сгрупированные по неделям"""

    cal = calendar.Calendar()

    # >>> cal.monthdatescalendar(2025, 10)
    # [[datetime.date(2025, 9, 29),
    #   datetime.date(2025, 9, 30),
    #   datetime.date(2025, 10, 1),
    #   datetime.date(2025, 10, 2),
    #   datetime.date(2025, 10, 3),
    #   datetime.date(2025, 10, 4),
    #   datetime.date(2025, 10, 5)],
    #  [datetime.date(2025, 10, 6),
    #   datetime.date(2025, 10, 7),
    #   datetime.date(2025, 10, 8),
    #   datetime.date(2025, 10, 9),
    #   datetime.date(2025, 10, 10),
    #   datetime.date(2025, 10, 11),
    #   datetime.date(2025, 10, 12)],
    #  ...]
    return cal.monthdatescalendar(year, month)


def _month_week():
    """Closure для month_week"""
    # кеш соответствия даты месяца и недели месяца
    # {(2025, 10): {(9, 29): 1, (9, 30): 1,
    #               (10, 1): 1, (10, 2): 1, (10, 3): 1, (10, 4): 1, (10, 5): 1, (10, 6): 2, (10, 7): 2,
    #               ...,
    #               (10, 31): 5, (11, 1): 5, (11, 2): 5},
    #  ...}
    day_week_map = {
    }

    def month_week(d, month):
        """Возвращает для даты номер недели внутри месяца"""

        year, month = d.year, month
        if (year, month) not in day_week_map:
            cal = calendar.Calendar()
            # для каждой даты календарного месяца посчитаем, какая это неделя
            day_week_map[(year, month)] = {
                (dt.month, dt.day): week
                for week, dates in enumerate(cal.monthdatescalendar(year, month), 1)
                for dt in dates
            }
        return day_week_map[(year, month)][(d.month, d.day)]

    return month_week

month_week = _month_week()


def get_cal_blocks(start_date, end_date):
    """Возвращает блоки дней для каждой недели события, не выходящие за рамки месяца"""

    # (datetime.date(2025, 10, 25), datetime.date(2025, 10, 28)) ->
    # [{'week': 4, 'start': 6, 'end': 7},
    #  {'week': 5, 'start': 1, 'end': 2}]
    # Т.е. для события с 25 по 28 октября 2025 вернется два блока:
    # сб, вс на 4 неделе и пн, вт для 5 недели
    month = start_date.month
    start_week = month_week(start_date, month)

    # последняя дата в месяце (может быть из следующего месяца)
    last_date = calendar.Calendar().monthdatescalendar(start_date.year, month)[-1][-1]

    dates = [
        dt
        for i in range((end_date - start_date).days + 1)
        # не выходим за границы календаря текущего месяца
        if (dt := start_date + timedelta(days=i)) <= last_date
    ]
    for week, group in groupby(dates, lambda d: month_week(d, month)):
        # если переходим в другой месяц, то заканчиваем
        if week < start_week:
            break
        block_dates = list(group)
        yield {'week': week, 'start': block_dates[0].isoweekday(), 'end': block_dates[-1].isoweekday()}


def make_cal_blocks(events):
    """Добавляет к событиям дополнительную информацию для отображения в календаре

    В какой день на неделе событие начинается и заканчивается.
    Если событие не умещается в 1 неделю, то оно разделится на нужное количество
    """
    # [
    #     {'name': 'Счастье Артиш + Кузьминич',
    #      'type': 'happiness',
    #      'pos': {'week': 3, 'start': 5, 'end': 7, 'index': 1}},
    #     {'name': 'YES!',
    #      'type': 'yes',
    #      'pos': {'week': 4, 'start': 6, 'end': 7, 'index': 1}},
    #     {'name': 'YES!',
    #      'type': 'yes',
    #      'pos': {'week': 5, 'start': 1, 'end': 2, 'index': 1}},
    # ]
    for e in events:
        # for i, block in enumerate(get_cal_blocks(e['dates'][0], e['dates'][-1]), 1):
        for i, block in enumerate(get_cal_blocks(e['start_date'].date(), e['end_date'].date()), 1):
            block['index'] = i
            yield e | {'pos': block}


def assign_levels(events):
    """Распределяет блоки/полоски событий по уровням

    Чтобы они помещались в неделю и не перекрывались на одном уровне
    """
    events = sorted(events, key=lambda e: e['pos']['start'])
    levels = []  # [(end, level_index), ...]
    next_level = 1

    for event in events:
        start, end = event['pos']['start'], event['pos']['end']

        # пробуем найти уровень, где текущее событие помещается
        for i, l in enumerate(levels, 1):
            if l[0] < start:
                levels[i-1] = (end, i)
                event['pos']['index'] = i
                break
        else:
            levels.append((end, next_level))
            event['pos']['index'] = next_level
            next_level += 1

    return events


def prepare_events(events):
    """Подготавливает события для отображения в календаре"""

    blocks = (e for e in make_cal_blocks(events))
    blocks = sorted(blocks, key=lambda e: (e['pos']['week'], e['pos']['start']))
    indexed = []
    for _, group in groupby(blocks, lambda e: e['pos']['week']):
        indexed.extend(assign_levels(group))

    return indexed
