"""Точка входа Passenger на serv00

Лежит в ~/domains/calendar.maxc4m.serv00.net/public_python/ рядом с settings_serv00.py,
сам календарь установлен в venv из wheel.
"""
import os
import sys

from django.core.wsgi import get_wsgi_application


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_serv00'

application = get_wsgi_application()
