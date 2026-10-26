"""Синхронизация событий с админкой artofliving.ru

Курсы планируются в календаре, а страница курса в админке сайта заводится, когда она нужна.
Здесь курсы из админки за месяц сопоставляются с событиями календаря: по admin_id или, если его
еще нет, по типу курса, датам и месту.
"""
from datetime import date, datetime
import logging
import re

from django.conf import settings
from django.db.models import Q

from .dates import Month, human_dates
from .models import Event, EventType, Place, Status, Teacher


logger = logging.getLogger(__name__)


PUBLIC_LINK_TEMPLATE = 'https://artofliving.ru/{event_path}?streamId={event_id}#offerBlock'


COURSE_NAME_TYPE = {
    'art excel': 'art_excel',
    'детский курс (art excel)': 'art_excel',
    'dsn': 'dsn',
    'дсн': 'dsn',
    'лидерский курс (dsn)': 'dsn',
    'vtp online': 'vtp_online',
    'yes!': 'yes',
    'подростковый курс (yes!)': 'yes',
    'yes+': 'yes_plus',
    'блессинг': 'blessing',
    'глубокий сон и снятие тревожности': 'deep_sleep',
    # 'забота о спине и коррекция осанки': 'spine_care',
    'забота о позвоночнике и осанке': 'healthy_posture',
    'здоровое питание': 'cooking',
    'искусство жизни — премиум': 'premium',
    'искусство медитации': 'meditation',
    'искусство тишины': 'silence',
    'искусство тишины online': 'silence_online',
    # 'искусство тишины интенсив': 'silence_intense',
    'йога': 'yoga',
    'йога для позвоночника': 'yoga_spine',
    'первый шаг': 'first_step',
    'песенный сатсанг': 'satsang',  # 🎸
    'победи зависимость': 'give_up_smoking',
    'поддерживающее занятие': 'practices',
    'поддерживающее занятие online': 'practices_online',
    'поддерживающее занятие для vtp': 'practices_vtp',
    'процесс вечности': 'eternity',
    'процесс интуиции': 'intuition',
    'процесс интуиции 5-8 лет': 'intuition_5_8',
    'процесс интуиции 8-18 лет': 'intuition_8_18',
    'саньям': 'sanyam',
    'саньям 2': 'sanyam2',
    'суставная йога': 'yoga_joints',
    'счастье': 'happiness',
    'счастье онлайн': 'happiness_online',
    # 'счастье (благотворительный)': 'happiness',
    'шри шри йога': 'ssy',
    'шри шри йога 2': 'ssy2',
}


# PATH - это path публичной ссылки на сайте
# TYPE - это тип курса из COURSE_NAME_TYPE
EVENT_TYPE_PATH = {
    'art_excel': "artexcel",
    'blessing': "blessing",
    'cooking': "cookie",
    'deep_sleep': "deep-sleep",
    'dsn': "dsn",
    'eternity': 'process_vechnosti',
    'first_step': "firststep",
    'give_up_smoking': "give-up-smoking",
    'happiness': "happiness",
    'healthy_posture': 'healthy-posture',
    'intuition': "intuition-process-8-18",
    'intuition_5_8': "intuition-process-5-7",
    'intuition_8_18': "intuition-process-8-18",
    'meditation': "meditation",
    'practices_online': "practice-online",
    'premium': "premium",
    'sanyam': 'sanyam',
    'sanyam2': 'sanyam2',
    'silence': "art-of-silence",
    'silence_online': "art-of-silence_online",
    'ssy': "yoga",
    'ssy2': "srisriyoga2",
    'vtp_online': "vtp_online",
    'yes': "yes",
    'yes_plus': "yesplus",
}


# написание имени → (фамилия, имя), если имя нельзя просто разделить по первому пробелу
TEACHER_NAMES = {
    'Татьяна Куликова': ('Куликова', 'Татьяна'),
    'Кашикар Динеш': ('Свами Каушик', '(Каши)'),
    'Свами Каушик (Каши)': ('Свами Каушик', '(Каши)'),
}

# в админке эти учителя уже записаны как «Фамилия Имя»
NOT_SWAPPED_TEACHERS = ['Коробко Анастасия', 'Кашикар Динеш']


class AdminLoginError(Exception):
    pass


def get_course_type(name):
    """Возвращает тип курса по названию из админки или None, если название неизвестно

    >>> get_course_type('Счастье')
    'happiness'
    """
    return COURSE_NAME_TYPE.get(name.lower())


def parse_dates(date_str, year):
    """Парсит строку в одну или две даты

    Примеры: '31 Октября-2 Ноября', '17-19 Октября', '19 Октября'.
    Возвращает список дат, например [date(2025, 10, 31), date(2025, 11, 2)].
    """
    # 1. '31 Октября-2 Ноября'
    pattern_full_range = r'(\d+)\s+([А-Яа-я]+)[-–](\d+)\s+([А-Яа-я]+)'
    # 2. '17-19 Октября'
    pattern_month_range = r'(\d+)[-–](\d+)\s+([А-Яа-я]+)'
    # 3. '19 Октября'
    pattern_single_date = r'(\d+)\s+([А-Яа-я]+)'

    if match := re.match(pattern_full_range, date_str, re.IGNORECASE):
        day1, month1, day2, month2 = match.groups()
        return [date(year, Month[month1.lower()].value, int(day1)),
                date(year, Month[month2.lower()].value, int(day2))]
    if match := re.match(pattern_month_range, date_str, re.IGNORECASE):
        day1, day2, month = match.groups()
        month = Month[month.lower()].value
        return [date(year, month, int(day1)), date(year, month, int(day2))]
    if match := re.match(pattern_single_date, date_str, re.IGNORECASE):
        day, month = match.groups()
        return [date(year, Month[month.lower()].value, int(day))]

    raise ValueError(f"Неизвестный формат строки: '{date_str}'")


def course_dates(date_str, year, month):
    """Даты курса из админки, найденного в поиске за month

    В строке дат года нет. Курс '29 декабря-2 января' может найтись и в декабре, и в январе.
    """
    dates = parse_dates(date_str, year)
    start, end = dates[0], dates[-1]
    # курс начался в декабре прошлого года, а ищем за январь
    if start.month - month > 6:
        start = start.replace(year=year - 1)
        if end.month - month > 6:
            end = end.replace(year=year - 1)
    # курс переходит на следующий год
    if end < start:
        end = end.replace(year=end.year + 1)
    return start, end


def swap_names(name):
    """Меняет 'имя фамилия' на 'фамилия имя' или наоборот"""
    name_parts = name.split()
    if len(name_parts) == 2:
        first, last = name_parts
        return f'{last} {first}'
    return name


def split_teacher_name(full_name):
    """'Фамилия Имя' → (фамилия, имя)"""
    if full_name in TEACHER_NAMES:
        return TEACHER_NAMES[full_name]
    last_name, _, first_name = full_name.partition(' ')
    return last_name, first_name


def get_public_link(event_type, admin_id):
    """Возвращает публичную ссылку на событие на сайте artofliving.ru"""
    if event_type in EVENT_TYPE_PATH:
        return PUBLIC_LINK_TEMPLATE.format(event_path=EVENT_TYPE_PATH[event_type], event_id=admin_id)
    return ''


def parse_admin_course(course, year, month):
    """Курс из админки (формат aa.proxy.admin.parse_courses) → словарь для синхронизации

    Все значения сериализуются в JSON, чтобы курсы можно было хранить в сессии.
    """
    start_date, end_date = course_dates(course['date'], year, month)
    course_type = get_course_type(course['name'])

    teachers = []
    if course.get('teachers'):
        for name in (t.strip() for t in course['teachers'].split(',')):
            name = name if name in NOT_SWAPPED_TEACHERS else swap_names(name)
            teachers.append(' '.join(split_teacher_name(name)).strip())

    return {
        'admin_id': course['id'],
        'admin_link': course['link'],
        'public_link': get_public_link(course_type, course['id']) if course_type else '',
        'name': course['name'],
        'type': course_type,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'place': course['place'],
        'teachers': teachers,
        'num_payments': course.get('num_payments'),
        'status': course.get('status'),
    }


def fetch_admin_courses(year, month):
    """Загружает курсы за месяц из админки artofliving.ru"""
    from aa.proxy.admin import OFFLINE_ADMIN_URL, find_courses, log_in

    if not (settings.AOL_ADMIN_EMAIL and settings.AOL_ADMIN_PASSWORD):
        raise AdminLoginError('Не заданы AOL_ADMIN_EMAIL и AOL_ADMIN_PASSWORD')

    session = log_in(settings.AOL_ADMIN_EMAIL, settings.AOL_ADMIN_PASSWORD)
    # с неверным паролем сайт все равно отвечает на вход успехом, но список курсов отдает с кодом 403
    # и без таблицы, а find_courses принимает его за пустой месяц
    resp = session.get(OFFLINE_ADMIN_URL) if session is not None else None
    if resp is None or resp.status_code != 200 or 'w0-container' not in resp.text:
        raise AdminLoginError('Не удалось войти в админку artofliving.ru, проверьте логин и пароль')

    courses = find_courses(session, month=datetime(year, month, 1), include_free=True)
    # неопубликованные курсы без оплат - черновики, их не переносим
    courses = [c for c in courses if not (c.get('status') == 'Не опубликован' and c.get('num_payments') == 0)]
    logger.info('Из админки за %02d.%d получено курсов: %d', month, year, len(courses))
    return [parse_admin_course(c, year, month) for c in courses]


def event_values(event: Event):
    """Значения события в том же виде, что у курса из parse_admin_course"""
    return {
        'name': event.type.name,
        'start_date': event.start_date.isoformat(),
        'end_date': event.end_date.isoformat(),
        'place': event.place.name,
        'teachers': [str(t) for t in event.teachers.all()],
        'num_payments': event.num_payments,
        'status': event.status.name if event.status else None,
        'admin_id': event.admin_id,
        'public_link': event.public_link,
    }


FIELD_LABELS = {
    'name': 'Курс',
    'start_date': 'Начало',
    'end_date': 'Окончание',
    'place': 'Место',
    'teachers': 'Учителя',
    'num_payments': 'Оплатили',
    'status': 'Статус',
    'admin_id': 'ID в админке',
    'public_link': 'Ссылка на сайте',
}


def course_changes(course, event: Event):
    """Какие поля события поменяются при обновлении из админки: [(название, было, стало), ...]"""
    old = event_values(event)
    changes = []
    for field, label in FIELD_LABELS.items():
        new_value = course[field]
        if field == 'teachers':
            # порядок учителей не храним
            if sorted(new_value) == sorted(old[field]):
                continue
        elif new_value == old[field] or (field == 'public_link' and not new_value):
            continue
        changes.append((label, old[field], new_value))
    return changes


def plan_sync(courses):
    """Предлагает для каждого курса из админки, что сделать с событиями календаря

    Возвращает список строк {'course', 'kind', 'options', 'default'}, где kind - update (есть событие
    с таким admin_id), match (есть похожие события без admin_id), new или unknown (тип курса не
    распознан). Варианты: 'event:<pk>' - обновить событие, 'new' - создать, 'skip' - пропустить.
    """
    events = Event.objects.select_related('type', 'place', 'status').prefetch_related('teachers')
    rows = []

    for course in courses:
        skip = {'value': 'skip', 'label': 'Пропустить'}
        new = {'value': 'new', 'label': 'Создать новое событие'}

        if course['type'] is None:
            rows.append({'course': course, 'kind': 'unknown', 'options': [skip], 'default': 'skip'})
            continue

        if (event := events.filter(admin_id=course['admin_id']).first()):
            option = {'value': f'event:{event.pk}', 'label': 'Обновить', 'event': event,
                      'changes': course_changes(course, event)}
            rows.append({'course': course, 'kind': 'update', 'options': [option, skip],
                         'default': option['value']})
            continue

        candidates = events.filter(
            Q(admin_id__isnull=True) | Q(admin_id=''),
            type__slug=course['type'],
            start_date=course['start_date'],
            end_date=course['end_date'],
        ).order_by('pk')
        same_place = [e for e in candidates if e.place.name == course['place']]
        other_place = [e for e in candidates if e.place.name != course['place']]

        options = [
            {'value': f'event:{e.pk}', 'label': 'Слить', 'event': e, 'changes': course_changes(course, e)}
            for e in same_place + other_place
        ]
        default = f'event:{same_place[0].pk}' if len(same_place) == 1 else 'new'
        rows.append({'course': course, 'kind': 'match' if options else 'new',
                     'options': options + [new, skip], 'default': default})

    for row in rows:
        start_date, end_date = (date.fromisoformat(row['course'][f]) for f in ['start_date', 'end_date'])
        row['dates'] = f'{human_dates(start_date, end_date)} {end_date.year}'

    return rows


def apply_course(course, event: Event | None = None):
    """Создает событие из курса админки или обновляет существующее"""
    event_type, _ = EventType.objects.get_or_create(slug=course['type'], defaults={'name': course['name']})
    place, _ = Place.objects.get_or_create(name=course['place'])
    status = Status.objects.get_or_create(name=course['status'])[0] if course['status'] else None

    if event is None:
        event = Event()
    event.type = event_type
    event.place = place
    event.status = status
    event.start_date = date.fromisoformat(course['start_date'])
    event.end_date = date.fromisoformat(course['end_date'])
    event.num_payments = course['num_payments']
    event.admin_id = course['admin_id']
    event.admin_link = course['admin_link']
    if course['public_link']:
        event.public_link = course['public_link']
    event.save()

    teachers = []
    for full_name in course['teachers']:
        last_name, first_name = split_teacher_name(full_name)
        teachers.append(Teacher.objects.get_or_create(last_name=last_name, first_name=first_name)[0])
    event.teachers.set(teachers)

    return event
