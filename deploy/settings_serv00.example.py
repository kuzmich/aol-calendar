"""Настройки календаря на serv00

Шаблон. На сервере лежит как public_python/settings_serv00.py (chmod 600) с заполненными
SECRET_KEY и паролем базы.
"""
from config.settings import *  # noqa: F403


DEBUG = False
SECRET_KEY = ''

ALLOWED_HOSTS = ['calendar.maxc4m.serv00.net']
CSRF_TRUSTED_ORIGINS = ['https://calendar.maxc4m.serv00.net']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# на HTTPS перенаправляет сам serv00: devil www options <домен> sslonly on

# календарь не отправляет почту, консольный бэкенд по умолчанию не мешает
SILENCED_SYSTEM_CHECKS = ['mail.E001']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'pgsql0.serv00.com',
        'PORT': '5432',
        'NAME': 'p7843_calendar',
        'USER': 'p7843_calendar',
        'PASSWORD': '',
    }
}

# вход в админку artofliving.ru для синхронизации курсов
AOL_ADMIN_EMAIL = ''
AOL_ADMIN_PASSWORD = ''

STATIC_URL = '/static/'
STATIC_ROOT = '/usr/home/maxc4m/domains/calendar.maxc4m.serv00.net/public_python/public/static'
