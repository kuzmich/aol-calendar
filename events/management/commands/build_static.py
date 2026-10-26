"""Генерирует статические страницы календаря для GitHub Pages"""
from pathlib import Path

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from events.calendar import YEARS, calendar_context


class Command(BaseCommand):
    help = 'Генерирует out/<год>.html из событий в базе'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', default='out', type=Path)

    def handle(self, *args, **options):
        output_dir: Path = options['output_dir']
        output_dir.mkdir(parents=True, exist_ok=True)

        for year in YEARS:
            output = render_to_string('events/page.html', calendar_context(year) | {'static_build': True})
            output_file = output_dir / f'{year}.html'
            output_file.write_text(output)
            self.stdout.write(f'Записано {len(output)} байт в файл {output_file}')
