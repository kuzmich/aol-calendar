"""Переносит события из MongoDB в Postgres

Команду можно запускать повторно: события ищутся по mongo_id и обновляются.
"""
from collections import Counter, defaultdict
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from aol_calendar.utils import get_config
from aol_calendar.utils.db import get_db
from events.models import Event, EventDay, EventType, Place, Status, Teacher
from events.sync import split_teacher_name


# правильные названия типов, у которых в базе несколько написаний
EVENT_TYPE_NAMES = {
    'art_excel': 'Детский курс (ART Excel)',
    'yes': 'Подростковый курс (YES!)',
}


class Command(BaseCommand):
    help = 'Переносит события из MongoDB (AOL_CALENDAR_CONFIG) в Postgres'

    def handle(self, *args, **options):
        config = get_config()
        docs = list(get_db(config.DB_URL, config.DB_NAME)['events'].find())
        self.stdout.write(f'Событий в MongoDB: {len(docs)}')

        self.created = Counter()
        self.updated = Counter()

        with transaction.atomic():
            types = self.import_types(docs)
            for doc in docs:
                self.import_event(doc, types)

        for model in [EventType, Place, Status, Teacher, Event, EventDay]:
            name = model._meta.verbose_name_plural
            self.stdout.write(f'{name}: всего {model.objects.count()}, '
                              f'создано {self.created[model]}, обновлено {self.updated[model]}')

    def count(self, model, created):
        (self.created if created else self.updated)[model] += 1

    def import_types(self, docs):
        # у некоторых типов несколько написаний названия, берем правильное или самое частое
        names = defaultdict(Counter)
        for doc in docs:
            names[doc['type']][doc['name']] += 1

        types = {}
        for slug, counter in names.items():
            name = EVENT_TYPE_NAMES.get(slug) or counter.most_common(1)[0][0]
            types[slug], created = EventType.objects.get_or_create(slug=slug, defaults={'name': name})
            if created:
                self.count(EventType, created)
        return types

    def get_teacher(self, full_name: str):
        last_name, first_name = split_teacher_name(full_name)
        teacher, created = Teacher.objects.get_or_create(last_name=last_name, first_name=first_name)
        if created:
            self.count(Teacher, created)
        return teacher

    def import_event(self, doc, types):
        place, created = Place.objects.get_or_create(name=doc['place'])
        if created:
            self.count(Place, created)

        status = None
        if doc.get('status'):
            status, created = Status.objects.get_or_create(name=doc['status'])
            if created:
                self.count(Status, created)

        start_date = doc['start_date'].date()
        event, created = Event.objects.update_or_create(
            mongo_id=str(doc['_id']),
            defaults={
                'type': types[doc['type']],
                'place': place,
                'status': status,
                'start_date': start_date,
                'end_date': doc['end_date'].date(),
                'num_payments': doc.get('num_payments'),
                'admin_id': doc.get('admin_id'),
                'admin_link': doc.get('admin_link', ''),
                'public_link': doc.get('public_link', ''),
            },
        )
        self.count(Event, created)

        event.teachers.set([self.get_teacher(t) for t in doc.get('teachers', [])])

        if doc.get('time'):
            if event.end_date != start_date:
                self.stderr.write(f'Время {doc["time"]} у многодневного события {event} '
                                  f'({doc["_id"]}) записано на первый день')
            _, created = EventDay.objects.update_or_create(
                event=event, date=start_date,
                defaults={'start_time': datetime.strptime(doc['time'], '%H:%M').time()},
            )
            self.count(EventDay, created)
