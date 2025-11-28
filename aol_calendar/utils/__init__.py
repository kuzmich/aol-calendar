from ..const import Month


def human_dates(start_date, end_date):
    """Форматирует даты начала и конца события в человеко-читаемом виде

    >>> human_dates(date(2026, 4, 29), date(2026, 5, 3))
    '29 апреля-3 мая'
    """
    month = start_date.month
    if not end_date or end_date == start_date:
        return f'{start_date.day} {Month(month).name}'
    else:
        month2 = end_date.month
        if month2 == month:
            return f'{start_date.day}-{end_date.day} {Month(month).name}'
        else:
            return f'{start_date.day} {Month(month).name}-{end_date.day} {Month(month2).name}'


def swap_name_and_last_name(full_name):
    last_name, name = full_name.split()
    return f'{name} {last_name}'
