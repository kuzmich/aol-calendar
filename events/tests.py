from datetime import date, time
from unittest import mock

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

from . import sync
from .calendar import calendar_context
from .models import Event, EventDay, EventType, Place, Status, Teacher


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

    def test_archive_year(self):
        # 2025 открывается по прямой ссылке (на нее ведет редирект со старого сайта), но не в навигации
        self.create_event(self.happiness, date(2025, 3, 7), date(2025, 3, 9))
        response = self.client.get('/2025.html')

        self.assertContains(response, 'data-dates="7-9 марта"')
        self.assertNotContains(response, 'href="2025.html"')
        self.assertContains(response, 'href="2026.html"')


def admin_course(**kwargs):
    """Курс в формате aa.proxy.admin.parse_courses"""
    return {
        'id': '500001',
        'link': 'https://artofliving.ru/pl/sales/offline-admin/stream?id=500001',
        'date': '6–8 Февраля',
        'place': 'Театральная, 17',
        'name': 'Счастье',
        'teachers': 'Ольга Шумакова, Анастасия Коробко',
        'num_payments': 12,
        'status': 'Стоит в расписании',
    } | kwargs


class ParseAdminCourseTest(SimpleTestCase):

    def test_course(self):
        course = sync.parse_admin_course(admin_course(), 2026, 2)

        self.assertEqual(course['type'], 'happiness')
        self.assertEqual((course['start_date'], course['end_date']), ('2026-02-06', '2026-02-08'))
        # «Имя Фамилия» → «Фамилия Имя», кроме учителей, записанных в админке наоборот
        self.assertEqual(course['teachers'], ['Шумакова Ольга', 'Коробко Анастасия'])
        self.assertEqual(course['public_link'], 'https://artofliving.ru/happiness?streamId=500001#offerBlock')

    def test_dates_across_new_year(self):
        # курс находится и в поиске за декабрь, и в поиске за январь
        for year, month in [(2026, 12), (2027, 1)]:
            course = sync.parse_admin_course(admin_course(date='30 Декабря-2 Января'), year, month)
            self.assertEqual((course['start_date'], course['end_date']), ('2026-12-30', '2027-01-02'))

    def test_unknown_course(self):
        course = sync.parse_admin_course(admin_course(name='Новый курс'), 2026, 2)

        self.assertIsNone(course['type'])
        self.assertEqual(course['public_link'], '')


class SyncTestCase(CalendarTestCase):

    def course(self, **kwargs):
        return sync.parse_admin_course(admin_course(**kwargs), 2026, 2)

    def plan(self, **kwargs):
        [row] = sync.plan_sync([self.course(**kwargs)])
        return row


class PlanSyncTest(SyncTestCase):

    def test_update_by_admin_id(self):
        event = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8),
                                  admin_id='500001', num_payments=10)
        row = self.plan()

        self.assertEqual(row['kind'], 'update')
        self.assertEqual(row['default'], f'event:{event.pk}')
        self.assertIn(('Оплатили', 10, 12), row['options'][0]['changes'])

    def test_match_same_place(self):
        event = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8))
        row = self.plan()

        self.assertEqual(row['kind'], 'match')
        self.assertEqual(row['default'], f'event:{event.pk}')

    def test_other_place_is_option_but_not_default(self):
        small_hall = Place.objects.create(name='Театральная, 17 (малый зал)')
        event = Event.objects.create(type=self.happiness, place=small_hall,
                                     start_date=date(2026, 2, 6), end_date=date(2026, 2, 8))
        row = self.plan()

        self.assertEqual(row['kind'], 'match')
        self.assertIn(f'event:{event.pk}', [o['value'] for o in row['options']])
        self.assertEqual(row['default'], 'new')

    def test_events_with_admin_id_are_not_candidates(self):
        self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8), admin_id='499999')
        row = self.plan()

        self.assertEqual(row['kind'], 'new')
        self.assertEqual(row['default'], 'new')

    def test_unknown_course(self):
        row = self.plan(name='Новый курс')

        self.assertEqual(row['kind'], 'unknown')
        self.assertEqual([o['value'] for o in row['options']], ['skip'])


class ApplyCourseTest(SyncTestCase):

    def test_create(self):
        event = sync.apply_course(self.course(place='Новое место'))

        self.assertEqual(event.type, self.happiness)
        self.assertEqual(event.place.name, 'Новое место')
        self.assertEqual(event.status.name, 'Стоит в расписании')
        self.assertEqual((event.admin_id, event.num_payments), ('500001', 12))
        self.assertEqual(sorted(str(t) for t in event.teachers.all()), ['Коробко Анастасия', 'Шумакова Ольга'])

    def test_update_keeps_days(self):
        event = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8))
        EventDay.objects.create(event=event, date=date(2026, 2, 6), start_time=time(18))
        sync.apply_course(self.course(), event)
        event.refresh_from_db()

        self.assertEqual(event.admin_id, '500001')
        self.assertEqual(event.days.count(), 1)
        self.assertEqual(Event.objects.count(), 1)


class SyncViewTest(SyncTestCase):
    url = '/admin/events/event/sync/'

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('admin'))

    @mock.patch('events.sync.fetch_admin_courses')
    def test_fetch_and_apply(self, fetch):
        event = self.create_event(self.happiness, date(2026, 2, 6), date(2026, 2, 8))
        fetch.return_value = [self.course(), self.course(id='500002', name='Йога', date='10 Февраля')]

        response = self.client.post(self.url, {'action': 'fetch', 'month': 2, 'year': 2026})
        fetch.assert_called_once_with(2026, 2)
        self.assertContains(response, 'Курсы в админке за Февраль 2026: 2')
        self.assertContains(response, f'value="event:{event.pk}"\n                         checked')

        response = self.client.post(self.url, {'action': 'apply', 'choice_500001': f'event:{event.pk}',
                                               'choice_500002': 'new'})
        self.assertRedirects(response, '/admin/events/event/?start_date__year=2026&start_date__month=2',
                             fetch_redirect_response=False)
        event.refresh_from_db()
        self.assertEqual(event.admin_id, '500001')
        self.assertTrue(Event.objects.filter(admin_id='500002', type=self.yoga).exists())
        self.assertEqual(Status.objects.count(), 1)

    @mock.patch('events.sync.fetch_admin_courses', side_effect=sync.AdminLoginError('Не удалось войти'))
    def test_login_error(self, fetch):
        response = self.client.post(self.url, {'action': 'fetch', 'month': 2, 'year': 2026}, follow=True)

        self.assertContains(response, 'Не удалось загрузить курсы из админки: Не удалось войти')

    def test_staff_only(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, f'/admin/login/?next={self.url}', fetch_redirect_response=False)
