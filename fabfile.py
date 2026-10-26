"""Деплой календаря на serv00: uv run fab deploy"""
from pathlib import Path
import tempfile

from fabric import task


hosts = ['serv00']

domain = 'calendar.maxc4m.serv00.net'
p_python = f'/usr/home/maxc4m/domains/{domain}/public_python'
venv = '/usr/home/maxc4m/venvs/aol-calendar'

# пакет aa (работа с админкой artofliving.ru) - соседний репозиторий, на PyPI его нет
aa_repo = Path('../automation')

# окружение для django-admin: settings_serv00.py лежит в public_python
django_env = f'cd {p_python} && PYTHONPATH={p_python} DJANGO_SETTINGS_MODULE=settings_serv00'


def install_wheel(c, whl_file: Path):
    c.put(str(whl_file), remote=f'{p_python}/')
    remote_whl = f'{p_python}/{whl_file.name}'
    c.run(f'{venv}/bin/pip install --quiet {remote_whl}')
    # версия не меняется, поэтому без --force-reinstall pip не обновит пакет
    c.run(f'{venv}/bin/pip install --quiet --force-reinstall --no-deps {remote_whl}')


@task(hosts=hosts)
def deploy(c):
    """Собирает wheel-ы aa и календаря, ставит их на сервер, применяет миграции и перезапускает сайт"""
    for old_whl in Path('dist').glob('*.whl'):
        old_whl.unlink()

    # aa собираем из закоммиченного состояния, без незаконченных правок в рабочей копии
    with tempfile.TemporaryDirectory() as aa_src:
        c.local(f'git -C {aa_repo} archive HEAD | tar -x -C {aa_src}')
        c.local(f'uv build --wheel --out-dir dist {aa_src}')
    c.local('uv build --wheel')

    install_wheel(c, next(Path('dist').glob('aa-*.whl')))
    install_wheel(c, next(Path('dist').glob('aol_calendar-*.whl')))

    manage(c, 'migrate')
    manage(c, 'collectstatic --noinput')
    c.run(f'devil www restart {domain}')


@task(hosts=hosts)
def manage(c, args):
    """Запускает команду django-admin на сервере: fab manage --args 'showmigrations'"""
    c.run(f'{django_env} {venv}/bin/django-admin {args}')
