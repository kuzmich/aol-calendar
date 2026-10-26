from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

from events.filters import teacher_names


def url(viewname, *args, **kwargs):
    return reverse(viewname, args=args or None, kwargs=kwargs or None)


def environment(**options):
    env = Environment(**options)
    env.globals.update(static=static, url=url)
    env.filters['teacher_names'] = teacher_names
    return env
