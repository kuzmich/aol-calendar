from datetime import date
import json
import logging
from pathlib import Path

from aa.proxy.admin import log_in, find_courses

from .cal import prepare_events
from .parsing import get_course_type, parse_dates


logger = logging.getLogger(__name__)


class AdminCourses:
    """Курсы из админки сайта artofliving.ru"""

    _sess = None

    def __init__(self, credentials, data_dir='data'):
        self.credentials = credentials
        self.data_dir = Path(data_dir)

    def parse_teachers(self, teachers_str):
        """Возвращает список фамилий учителей

        >>> adm._parse_teachers('Анжелика Артиш, Алексей Кузьминич')
        ['Артиш', 'Кузьминич']
        """
        teachers = []
        teachers_str = teachers_str.strip()
        if not teachers_str:
            return teachers
        for teacher in teachers_str.split(','):
            teachers.append(teacher.strip().split()[-1])
        return teachers

    @property
    def session(self):
        if not self._sess:
            self._sess = log_in(*self.credentials)
        return self._sess

    def get_courses(self, year, month, include_free=False):
        # [{'name': 'Блессинг',
        #   'date': '31 Октября-2 Ноября',
        #   'place': 'Театральная, 17',
        #   'teachers': 'Ольга Шумакова',
        #   'num_payments': 9,
        #   'status': 'Стоит в расписании'},
        #  {'name': 'Счастье', 'date': '17-19 Октября', 'place': 'Театральная, 17',
        #   'teachers': 'Анжелика Артиш, Алексей Кузьминич', 'num_payments': 10, 'status': 'Завершён'},
        #  {'name': 'YES!', 'date': '25–28 Октября', 'place': 'Театральная, 17',
        #   'teachers': 'Галина Дианова, Татьяна Шпикалова', 'num_payments': 9, 'status': 'Идет'}
        #  {'name': 'Поддерживающее занятие online', 'date': '19 Октября', 'place': 'Онлайн, время МСК+5',
        #   'num_payments': 9, 'status': 'Завершён'},
        return find_courses(self.session, month=date(year, month, 1), include_free=include_free)

    def parse(self, courses):
        # [
        #     {'name': 'Счастье',
        #      'type': 'happiness',
        #      'teachers': ['Артиш', 'Кузьминич'],
        #      'dates': [date(2025, 10, 17), date(2025, 10, 19)]},
        #     ...
        # ]
        for c in courses:
            data = {
                'name': c['name'],
                'type': get_course_type(c['name']),
                'dates': parse_dates(c['date'], year),
                'dates_str': c['date'],
                'place': c['place'],
                'teachers': self.parse_teachers(c.get('teachers', '')),
                'teachers_str': c.get('teachers', ''),
                'num_payments': c.get('num_payments', None),
            }
            if 'time' in c:
                data['time'] = c['time']
            yield data

    def prepare(self, events):
        actual = (e for e in events if not (e.get('status') == "Не опубликован" and e.get('num_payments') == 0))
        parsed = (e for e in self.parse(actual))
        # parsed = (e for e in parsed if e['type'] != 'practices')  # временно уберем поддерживающие занятия
        return prepare_events(parsed)

    def save(self, filename, courses):
        with filename.open('wt') as f:
            json.dump(courses, f, indent=2, ensure_ascii=False)

    def load(self, filename):
        with filename.open('rt') as f:
            return json.load(f)

    def get(self, year, month):
        admin_file = self.data_dir / f'{year}_{month}.json'
        manual_file = self.data_dir / 'manual' / f'{year}_{month}.json'
        events = []

        if admin_file.exists():
            try:
                events = self.load(admin_file)
            except Exception as e:
                logger.warning("Не могу загрузить data-файл : %s", admin_file, e)
        else:
            events = self.get_courses(year, month)
            self.save(admin_file, events)

        if manual_file.exists():
            try:
                events.extend(self.load(manual_file))
            except Exception as e:
                logger.warning("Не могу загрузить data-файл : %s", manual_file, e)

        return self.prepare(events)
