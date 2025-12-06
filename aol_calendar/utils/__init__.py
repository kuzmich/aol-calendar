import importlib.util
import os
import sys

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


def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_config_path(config_var='AOL_CALENDAR_CONFIG'):
    return os.environ[config_var]


def get_config():
    config_path = get_config_path()
    return import_from_path('aol_calendar_config', config_path)
