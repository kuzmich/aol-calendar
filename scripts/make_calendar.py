import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from aol_calendar.const import MonthName
from aol_calendar.filters import teacher_names
from aol_calendar.utils.cal import prepare_events, get_month_dates
from aol_calendar.utils.db import get_events


logger = logging.getLogger(__name__)


def render_calendar(context, template_file):
    env = Environment(
        loader=FileSystemLoader("aol_calendar/templates"),
        autoescape=select_autoescape()
    )
    env.filters['teacher_names'] = teacher_names
    template = env.get_template(template_file)
    return template.render(context)


def write_to_file(output, output_file):
    with open(output_file, 'wt') as f:
        f.write(output)

    logger.info('Записано %d байт в файл %s', len(output), output_file)


if __name__ == "__main__":
    logging.basicConfig(level='DEBUG')
    logging.getLogger('pymongo').setLevel('INFO')

    template_file = 'page.html'
    output_dir = 'out/'

    years = [2025, 2026]

    for year in years:
        calendar_data = []

        for month in range(1, 12+1):
            calendar_data.append({
                'dates': get_month_dates(year, month),
                'events': prepare_events(get_events(year, month)),
                'month': month,
                'month_name': MonthName(month).name.title(),
                'year': year
            })

        output = render_calendar(
            {'calendar_data': calendar_data,
             'years': years,
             'current_year': year},
            template_file
        )
        write_to_file(output, Path(output_dir) / f'{year}.html')
