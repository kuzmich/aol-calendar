from datetime import datetime

from flask import request, redirect, url_for, render_template, abort, Blueprint

from .const import MonthName
from .forms import EventForm
from .utils import human_dates
from .utils.db import get_events, add_events, get_event_by_id, save_event, delete_event
from .utils.cal import prepare_events, get_month_dates,  weekdays_in_month
from .vars import EVENTS


bp = Blueprint('cal', __name__, url_prefix='/')


def make_event(form_data, **override):
    """Подготавливает данные из формы добавления/редактирования для сохранения в базу"""

    data = form_data | override

    event_data = {
        "name": EVENTS[data["event_type"]],
        "type": data["event_type"],
        "dates": human_dates(data["start_date"], data["end_date"]),
        "place": data["place"],
        "start_date": datetime.combine(data["start_date"], datetime.min.time()),
        "end_date": datetime.combine(data["end_date"] or data["start_date"], datetime.min.time()),
    }

    if data['teachers']:
        event_data["teachers"] = data["teachers"]
    if data['start_time']:
        event_data["time"] = data["start_time"].strftime('%H:%M')

    return event_data


def make_recurring_events(form_data):
    start_date = form_data['start_date']
    end_date = form_data['end_date']

    for weekday in form_data['schedule']:
        for event_dt in weekdays_in_month(start_date.year, start_date.month, weekday - 1):
            if event_dt >= start_date and (event_dt <= end_date if end_date else True):
                yield make_event(form_data, start_date=event_dt, end_date=event_dt)


@bp.route("/")
def home_page():
    return redirect(url_for('cal.calendar_page', year=datetime.now().year))


@bp.route("/<int:year>.html")
def calendar_page(year):
    years = [2025, 2026]
    calendar_data = []
    form = EventForm()

    for month in range(1, 12+1):
        calendar_data.append({
            'dates': get_month_dates(year, month),
            'events': prepare_events(get_events(year, month)),
            'month': month,
            'month_name': MonthName(month).name.title(),
            'year': year
        })

    return render_template(
        'page.html',
        calendar_data=calendar_data,
        years=years,
        current_year=year,
        # флаг админского интерфейса - добавление/редактирование событий
        can_edit=True,
        # переменные формы добавления события
        form_url=url_for('cal.add_event'),
        form=form,
    )


@bp.route("/events/", methods=["POST"])
def add_event():
    """Добавление события"""

    form = EventForm(request.form)

    start_date = form.start_date.data
    year = start_date.year
    month = start_date.month

    if request.method == "POST" and form.validate():
        event_type = form.event_type.data
        schedule = form.schedule.data

        if (event_type.startswith("practices") or event_type.startswith("yoga")) and schedule:
            events = list(make_recurring_events(form.data))
            for event in events:
                print(event)
            add_events(events)
        else:
            event = make_event(form.data)
            print(event)
            add_events([event])

        return redirect(url_for('cal.calendar_page', year=year, _anchor=str(month)))
    else:
        return render_template(
            "event-form.html",
            form_url=url_for('cal.add_event'),
            form=form,
            edit=False,
        )


@bp.route("/events/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    """Редактирование события"""

    event = get_event_by_id(event_id)
    if not event:
        abort(404)

    if request.method == "GET":
        # покажем форму редактирования события
        start_time = None
        if event.get('time'):
            start_time = datetime.strptime(event['time'], "%H:%M")
        form = EventForm(data=event, event_type=event['type'], start_time=start_time)
    else:
        if request.form.get('event-action') == 'delete':
            # удалим событие
            delete_event(event_id)
            start_date = event['start_date']
            return redirect(url_for('cal.calendar_page', year=start_date.year, _anchor=str(start_date.month)))

        # сохраним изменения или покажем форму редактирования с ошибками
        form = EventForm(request.form, data=event)
        if form.validate():
            save_event(event_id, make_event(form.data))
            start_date = event['start_date']
            return redirect(url_for('cal.calendar_page', year=start_date.year, _anchor=str(start_date.month)))

    return render_template(
        "event-form.html",
        form_url=url_for('cal.edit_event', event_id=event_id),
        form=form,
        edit=True,
    )
