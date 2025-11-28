from wtforms import Form, SelectField, SelectMultipleField, DateField, TimeField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import CheckboxInput, ListWidget

from .const import WeekDay
from .vars import EVENTS, LOCATIONS, TEACHERS


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class EventForm(Form):
    event_type = SelectField('Мероприятие', [DataRequired()], choices=list(EVENTS.items()), name="type")
    start_date = DateField('Дата начала', [DataRequired()], name="start-date")
    end_date = DateField('Дата окончания', [Optional()], name="end-date")
    schedule = MultiCheckboxField('Расписание', [Optional()], choices=WeekDay.choices(), coerce=int)
    start_time = TimeField('Время начала', [Optional()], name="start-time")
    place = SelectField('Место', [DataRequired()], choices=LOCATIONS)
    teachers = SelectMultipleField('Учителя', [Optional()], choices=TEACHERS)
