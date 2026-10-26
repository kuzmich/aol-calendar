"""Подготовка данных для страницы календаря на год"""
import calendar
from datetime import date

from django.urls import reverse

from aol_calendar.const import MonthName
from aol_calendar.utils import human_dates
from aol_calendar.utils.cal import get_month_dates, prepare_events
from .models import Event, EventDay


YEARS = [2026, 2027]

# персональные курсы медитации для 1 человека не показываем
EXCLUDED_ADMIN_IDS = ['492126', '492127', '492128']


def format_time(day: EventDay):
    return '–'.join(t.strftime('%H:%M') for t in (day.start_time, day.end_time) if t)


def event_time(event: Event):
    """Время проведения: '09:00' для одного дня или '6.02 18:00; 7.02 09:00–17:00' для нескольких"""

    days = [day for day in event.days.all() if day.start_time or day.end_time]
    if len(days) == 1 and days[0].date == event.start_date == event.end_date:
        return format_time(days[0])
    return '; '.join(f'{day.date.day}.{day.date.month:02} {format_time(day)}' for day in days)


def event_data(event: Event):
    """Событие в формате, который ждут шаблон и prepare_events"""

    return {
        'id': event.pk,
        'type': event.type.slug,
        'name': event.type.name,
        'dates': human_dates(event.start_date, event.end_date),
        'time': event_time(event),
        'place': event.place.name,
        'teachers': [str(t) for t in event.teachers.all()],
        'num_payments': event.num_payments,
        'public_link': event.public_link,
        'start_date': event.start_date,
        'end_date': event.end_date,
        'admin_url': reverse('admin:events_event_change', args=[event.pk]),
    }


def get_events(year):
    """События, которые хотя бы одним днем попадают в год"""

    events = (
        Event.objects
        .filter(start_date__lte=date(year, 12, 31), end_date__gte=date(year, 1, 1))
        .exclude(admin_id__in=EXCLUDED_ADMIN_IDS)
        .select_related('type', 'place')
        .prefetch_related('teachers', 'days')
        .order_by('start_date', 'pk')
    )
    return [event_data(e) for e in events]


def calendar_context(year):
    events = get_events(year)
    calendar_data = []

    for month in range(1, 12+1):
        month_start = date(year, month, 1)
        month_end = date(year, month, calendar.monthrange(year, month)[1])
        # событие может начаться в предыдущем месяце и закончиться в следующем
        month_events = [e for e in events if e['start_date'] <= month_end and e['end_date'] >= month_start]

        calendar_data.append({
            'dates': get_month_dates(year, month),
            'events': prepare_events(month_events, year, month),
            'month': month,
            'month_name': MonthName(month).name.title(),
            'year': year,
        })

    return {
        'calendar_data': calendar_data,
        'years': YEARS,
        'current_year': year,
    }
