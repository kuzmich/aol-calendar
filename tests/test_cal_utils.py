from datetime import datetime, date
from pprint import pprint as pp

from aol_calendar.utils.cal import get_cal_blocks


class TestGetCalBlocks:

    def test_same_month_dates(self):
        blocks = list(get_cal_blocks(date(2025, 10, 25), date(2025, 10, 28)))
        print(blocks)
        assert [
            {'week': 4, 'start': 6, 'end': 7},
            {'week': 5, 'start': 1, 'end': 2}
        ] == blocks

    def test_start_date_in_cur_or_prev_month(self):
        blocks = list(get_cal_blocks(date(2026, 10, 30), date(2026, 11, 15), 10))
        print(blocks)
        assert [
            {'week': 5, 'start': 5, 'end': 7},
        ] == blocks

        blocks = list(get_cal_blocks(date(2026, 10, 30), date(2026, 11, 15), 11))
        print(blocks)
        assert [
            {'week': 1, 'start': 5, 'end': 7},
            {'week': 2, 'start': 1, 'end': 7},
            {'week': 3, 'start': 1, 'end': 7},
        ] == blocks

    def test_start_date_in_prev_year(self):
        blocks = list(get_cal_blocks(date(2025, 12, 30), date(2026, 1, 2), 1, 2026))
        print(blocks)
        assert [
            {'week': 1, 'start': 2, 'end': 5},
        ] == blocks

    def test_end_date_in_next_month_2(self):
        blocks = list(get_cal_blocks(date(2025, 10, 25), date(2025, 11, 4), 10))
        print(blocks)
        assert [
            {'week': 4, 'start': 6, 'end': 7},
            {'week': 5, 'start': 1, 'end': 7},
        ] == blocks

        blocks = list(get_cal_blocks(date(2025, 10, 25), date(2025, 11, 4), 11))
        print(blocks)
        assert [
            {'week': 1, 'start': 1, 'end': 7},
            {'week': 2, 'start': 1, 'end': 2},
        ] == blocks
