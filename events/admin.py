from collections import Counter
from datetime import date
import logging

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from . import sync
from .dates import MonthName
from .models import Event, EventDay, EventType, Place, Status, Teacher


logger = logging.getLogger(__name__)


# короткие еженедельные занятия, из-за которых в списке не видно основных курсов
REGULAR_EVENT_TYPES = ['practices', 'practices_online', 'practices_vtp', 'yoga', 'yoga_spine', 'yoga_joints']


class EventKindFilter(admin.SimpleListFilter):
    title = 'вид события'
    parameter_name = 'kind'

    def lookups(self, request, model_admin):
        return [
            ('courses', 'Курсы'),
            ('regular', 'Регулярные занятия'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'courses':
            return queryset.exclude(type__slug__in=REGULAR_EVENT_TYPES)
        if self.value() == 'regular':
            return queryset.filter(type__slug__in=REGULAR_EVENT_TYPES)
        return queryset


class SyncMonthForm(forms.Form):
    month = forms.TypedChoiceField(label='Месяц', coerce=int,
                                   choices=[(m, MonthName(m).name.title()) for m in range(1, 13)])
    year = forms.IntegerField(label='Год', min_value=2024, max_value=2100)


class EventDayInline(admin.TabularInline):
    model = EventDay
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['type', 'start_date', 'end_date', 'place', 'status', 'num_payments', 'teacher_names']
    list_filter = [EventKindFilter, 'type', 'status', 'place']
    list_select_related = ['type', 'place', 'status']
    date_hierarchy = 'start_date'
    search_fields = ['type__name', 'place__name', 'teachers__last_name', 'admin_id']
    filter_horizontal = ['teachers']
    inlines = [EventDayInline]
    # кнопка «Синхронизация с админкой»
    change_list_template = 'admin/events/event/change_list.html'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('teachers')

    @admin.display(description='Учителя')
    def teacher_names(self, obj):
        return ', '.join(str(t) for t in obj.teachers.all())

    def get_urls(self):
        sync_url = path('sync/', self.admin_site.admin_view(self.sync_view), name='events_event_sync')
        return [sync_url] + super().get_urls()

    def sync_view(self, request):
        """Синхронизация с админкой artofliving.ru: загрузить месяц, проверить, применить"""
        if not (self.has_add_permission(request) and self.has_change_permission(request)):
            raise PermissionDenied

        today = date.today()
        form = SyncMonthForm(request.POST or None, initial={'month': today.month, 'year': today.year})
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Синхронизация с админкой artofliving.ru',
            'form': form,
        }
        action = request.POST.get('action')

        if action == 'fetch' and form.is_valid():
            year, month = form.cleaned_data['year'], form.cleaned_data['month']
            try:
                courses = sync.fetch_admin_courses(year, month)
            except Exception as e:
                logger.exception('Не удалось загрузить курсы из админки')
                messages.error(request, f'Не удалось загрузить курсы из админки: {e}')
            else:
                request.session['events_sync'] = {'year': year, 'month': month, 'courses': courses}
                context['rows'] = sync.plan_sync(courses)
                context['period'] = f'{MonthName(month).name.title()} {year}'

        elif action == 'apply':
            data = request.session.pop('events_sync', None)
            if not data:
                messages.error(request, 'Курсы из админки не найдены, загрузите их еще раз')
                return redirect('admin:events_event_sync')

            result = Counter()
            used_events = set()
            with transaction.atomic():
                for row in sync.plan_sync(data['courses']):
                    course = row['course']
                    options = {option['value']: option for option in row['options']}
                    choice = request.POST.get(f'choice_{course["admin_id"]}', 'skip')
                    # с одним событием можно слить только один курс из админки
                    if choice not in options or choice == 'skip' or choice in used_events:
                        result['пропущено'] += 1
                    elif choice == 'new':
                        sync.apply_course(course)
                        result['создано'] += 1
                    else:
                        sync.apply_course(course, options[choice]['event'])
                        used_events.add(choice)
                        result['обновлено'] += 1

            messages.success(request, 'Синхронизация завершена: ' + ', '.join(
                f'{name} {result[name]}' for name in ['обновлено', 'создано', 'пропущено']))
            changelist_url = reverse('admin:events_event_changelist')
            return redirect(f'{changelist_url}?start_date__year={data["year"]}&start_date__month={data["month"]}')

        return TemplateResponse(request, 'admin/events/event/sync.html', context)


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name', 'slug']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name']
    search_fields = ['last_name', 'first_name']


@admin.register(Place, Status)
class NameAdmin(admin.ModelAdmin):
    search_fields = ['name']
