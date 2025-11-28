from .utils.db import (get_all_event_names_types, get_all_teachers, get_all_locations,
                      get_manual_entries, sort_locations, sort_events)


EVENTS = dict([("", "Не выбрано")] + sorted(
    set(get_all_event_names_types() + list(get_manual_entries('events.json', {}).items())),
    key=sort_events
))
TEACHERS = sorted(set(get_all_teachers() + get_manual_entries('teachers.json')))
LOCATIONS = ["Не выбрано"] + sorted(
    set(get_all_locations() + get_manual_entries('locations.json')),
    key=sort_locations
)
