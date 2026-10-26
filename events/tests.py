from datetime import date, time
from pathlib import Path
import tempfile

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from .calendar import calendar_context
from .models import Event, EventDay, EventType, Place, Teacher


class CalendarTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.place = Place.objects.create(name='Театральная, 17')
        cls.happiness = EventType.objects.create(slug='happiness', name='Счастье')
        cls.yoga = EventType.objects.create(slug='yoga', name='Йога')

    def create_event(self, event_type, start_date, end_date=None, **kwargs):
        return Event.objects.create(type=event_type, place=self.place, start_date=start_date,
                                    end_date=end_date or start_date, **kwargs)

    def month_events(self, year, month):
        return calendar_context(year)['calendar_data'][month - 1]['events']


class CalendarContextTest(CalendarTestCase):

    def test_event_position(self):
        # 6-8 февраля 2026 - пт-вс второй недели февраля (1 февраля - воскресенье)
        event = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8))
        event.teachers.add(Teacher.objects.create(last_name='Шумакова', first_name='Ольга'))

        [block] = self.month_events(2026, 2)
        self.assertEqual(block['pos'], {'week': 2, 'start': 5, 'end': 7, 'index': 1})
        self.assertEqual(block['name'], 'Счастье')
        self.assertEqual(block['dates'], '6-8 февраля')
        self.assertEqual(block['teachers'], ['Шумакова Ольга'])

    def test_event_spanning_months(self):
        self.create_event(self.happiness, date(2026, 1, 30), date(2026, 3, 2))

        for month in [1, 2, 3]:
            self.assertTrue(self.month_events(2026, month), f'Нет события в месяце {month}')

    def test_excluded_admin_ids(self):
        self.create_event(self.happiness, date(2026, 2, 6), admin_id='492126')

        self.assertEqual(self.month_events(2026, 2), [])

    def test_time(self):
        one_day = self.create_event(self.yoga, date(2026, 2, 3))
        EventDay.objects.create(event=one_day, date=one_day.start_date, start_time=time(9))
        course = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 7))
        EventDay.objects.create(event=course, date=date(2026, 2, 6), start_time=time(18), end_time=time(21))
        EventDay.objects.create(event=course, date=date(2026, 2, 7), start_time=time(9))

        times = {e['type']: e['time'] for e in self.month_events(2026, 2)}
        self.assertEqual(times, {'yoga': '09:00', 'happiness': '6.02 18:00–21:00; 7.02 09:00'})


class CalendarPageTest(CalendarTestCase):

    def setUp(self):
        self.event = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8))

    def test_page(self):
        response = self.client.get('/2026.html')

        self.assertContains(response, 'grid-row: 3; grid-column: 5 / 8')
        self.assertNotContains(response, 'data-admin-url')
        self.assertNotContains(response, 'add-event-btn')

    def test_unknown_year(self):
        self.assertEqual(self.client.get('/1999.html').status_code, 404)

    def test_staff_sees_admin_links(self):
        self.client.force_login(User.objects.create_user('staff', is_staff=True))
        response = self.client.get('/2026.html')

        self.assertContains(response, f'data-admin-url="/admin/events/event/{self.event.pk}/change/"')
        self.assertContains(response, 'href="/admin/events/event/add/"')

    def test_build_static(self):
        with tempfile.TemporaryDirectory() as output_dir:
            call_command('build_static', output_dir=Path(output_dir), stdout=open('/dev/null', 'w'))
            html = (Path(output_dir) / '2026.html').read_text()

        self.assertIn('href="calendar.css?ver=', html)
        self.assertIn('grid-row: 3; grid-column: 5 / 8', html)
        self.assertNotIn('/admin/', html)
