from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models

from .dates import human_dates

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


class EventType(models.Model):
    """Тип и название курса"""

    # используется в CSS для цвета и в фильтрах календаря
    slug = models.SlugField('Тип', unique=True)
    name = models.CharField('Название', max_length=200)

    class Meta:
        verbose_name = 'Тип курса'
        verbose_name_plural = 'Типы курсов'
        ordering = ['name']

    def __str__(self):
        return self.name


class Place(models.Model):
    name = models.CharField('Название', max_length=300, unique=True)

    class Meta:
        verbose_name = 'Место проведения'
        verbose_name_plural = 'Места проведения'
        ordering = ['name']

    def __str__(self):
        return self.name


class Teacher(models.Model):
    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Учитель'
        verbose_name_plural = 'Учителя'
        ordering = ['last_name', 'first_name']
        constraints = [
            models.UniqueConstraint(fields=['last_name', 'first_name'], name='unique_teacher_name'),
        ]

    def __str__(self):
        return f'{self.last_name} {self.first_name}'.strip()


class Status(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Статус'
        verbose_name_plural = 'Статусы'
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    type = models.ForeignKey(EventType, models.PROTECT, verbose_name='Курс', related_name='events')
    place = models.ForeignKey(Place, models.PROTECT, verbose_name='Место', related_name='events')
    status = models.ForeignKey(Status, models.PROTECT, verbose_name='Статус', related_name='events',
                               null=True, blank=True)
    start_date = models.DateField('Дата начала')
    end_date = models.DateField('Дата окончания')
    teachers = models.ManyToManyField(Teacher, verbose_name='Учителя', related_name='events', blank=True)
    num_payments = models.PositiveIntegerField('Количество оплативших', null=True, blank=True)

    # поток в админке artofliving.ru
    admin_id = models.CharField('ID в админке', max_length=20, unique=True, null=True, blank=True)
    admin_link = models.URLField('Ссылка в админке', blank=True)
    public_link = models.URLField('Ссылка на сайте', blank=True)

    # _id документа в MongoDB, из которой перенесены события (дамп: dump/mongo-2026-10-26.archive.gz)
    mongo_id = models.CharField(max_length=24, unique=True, null=True, blank=True, editable=False)

    if TYPE_CHECKING:
        days: RelatedManager['EventDay']

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['start_date', 'type__name']
        constraints = [
            models.CheckConstraint(condition=models.Q(end_date__gte=models.F('start_date')),
                                   name='event_end_date_gte_start_date'),
        ]

    def __str__(self):
        return f'{self.type}, {human_dates(self.start_date, self.end_date)} {self.end_date.year}'

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'Дата окончания раньше даты начала'})


class EventDay(models.Model):
    """Время проведения события в конкретный день

    Заполняется только для дней, у которых известно время. У многодневного события время
    может быть разным в разные дни.
    """

    event = models.ForeignKey(Event, models.CASCADE, verbose_name='Событие', related_name='days')
    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала', null=True, blank=True)
    end_time = models.TimeField('Время окончания', null=True, blank=True)

    class Meta:
        verbose_name = 'День события'
        verbose_name_plural = 'Дни события'
        ordering = ['date']
        constraints = [
            models.UniqueConstraint(fields=['event', 'date'], name='unique_event_day'),
        ]

    def __str__(self):
        times = '–'.join(t.strftime('%H:%M') for t in (self.start_time, self.end_time) if t)
        return f'{self.date:%d.%m.%Y} {times}'.strip()

    def clean(self):
        event = self.event
        if self.date and not (event.start_date <= self.date <= event.end_date):
            raise ValidationError({'date': 'Дата вне дат проведения события'})
        if self.start_time and self.end_time and self.end_time < self.start_time:
            raise ValidationError({'end_time': 'Время окончания раньше времени начала'})
