"""Деплой календаря на serv00: uv run fab deploy"""
from pathlib import Path

from fabric import task


hosts = ['serv00']

domain = 'calendar.maxc4m.serv00.net'
p_python = f'/usr/home/maxc4m/domains/{domain}/public_python'
venv = '/usr/home/maxc4m/venvs/aol-calendar'

# окружение для django-admin: settings_serv00.py лежит в public_python
django_env = f'cd {p_python} && PYTHONPATH={p_python} DJANGO_SETTINGS_MODULE=settings_serv00'


@task(hosts=hosts)
def deploy(c):
    """Собирает wheel, ставит его на сервер, применяет миграции и перезапускает сайт"""
    for old_whl in Path('dist').glob('*.whl'):
        old_whl.unlink()
    c.local('uv build --wheel')
    whl_file = next(Path('dist').glob('*.whl'))

    c.put(str(whl_file), remote=f'{p_python}/')
    remote_whl = f'{p_python}/{whl_file.name}'
    c.run(f'{venv}/bin/pip install --quiet {remote_whl}')
    # версия не меняется, поэтому без --force-reinstall pip не обновит пакет
    c.run(f'{venv}/bin/pip install --quiet --force-reinstall --no-deps {remote_whl}')

    manage(c, 'migrate')
    manage(c, 'collectstatic --noinput')
    c.run(f'devil www restart {domain}')


@task(hosts=hosts)
def manage(c, args):
    """Запускает команду django-admin на сервере: fab manage --args 'showmigrations'"""
    c.run(f'{django_env} {venv}/bin/django-admin {args}')
