# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Calendar of Art of Living courses and events in Irkutsk. Data lives in MongoDB; it is edited through a Flask app and published as static HTML on GitHub Pages. User-facing text, docstrings, comments and commit messages are in Russian.

## Commands

```bash
docker compose up -d                                            # MongoDB 8.2 on 127.0.0.1:27017
uv run --env-file .env flask --app aol_calendar run --debug     # editing site (Flask)
uv run --env-file .env scripts/make_calendar.py                 # regenerate out/<year>.html
uv run --env-file .env scripts/sync_events.py <year> <month>    # pull courses from artofliving.ru admin, merge into DB
uv run pytest                                                   # tests
uv run pytest tests/test_cal_utils.py::TestGetCalBlocks::test_same_month_dates
```

- `.env` sets `AOL_CALENDAR_CONFIG`, the path to a Python config module (`instance/config.py`) with `DB_URL`, `DB_NAME`, `EMAIL`, `PASSWORD`. Scripts load it via `aol_calendar.utils.get_config()`; the Flask app reads the same `instance/config.py` via `from_pyfile`.
- The `aa` dependency is a local editable package at `../automation` (provides `aa.proxy.admin` login/scraping for the artofliving.ru admin). `uv sync` fails without that sibling checkout.
- Deployment: pushing to `master` triggers `.github/workflows/static.yml`, which publishes `out/` to GitHub Pages. So `out/*.html` is committed; "data:" commits are typically sync + regenerate + commit of `out/`.

## Architecture

**Data flow:** artofliving.ru admin → `sync_events.py` (`utils/admin.AdminCourses` fetches, `utils/parsing.parse_admin_event` normalizes) → MongoDB `events` collection ← Flask form (`cal.py` add/edit/delete). Then `make_calendar.py` and the Flask `/<year>.html` route both render `templates/page.html` from the DB using the same pipeline.

**Rendering pipeline** (`utils/cal.py`): for each month, `get_events(year, month)` returns events whose start *or* end falls in the month → `prepare_events` splits each event into per-week blocks (`get_cal_blocks`, clipped to the month) and assigns stacking `level`s for overlapping events (`assign_levels`). The template positions blocks with CSS Grid `grid-row`/`grid-column`, stacking levels via margin. Flask passes `can_edit=True` (edit form/dialog); the static generator doesn't, so the public pages are read-only.

**Course types:** every event has a `type` slug used for colors (CSS) and filters (JS). `const.COURSE_NAME_TYPE` maps lowercased admin course names → type; unknown names log a warning and become `unknown`. When adding a new course name, add it there (and `EVENT_TYPE_PATH` for the public link, plus CSS color if needed). Each name should map to exactly one type. `docs/FORMAT.md` documents the DB, form, and legacy data-file formats.

**Sync merge logic** (`scripts/sync_events.py`): match by `admin_id` → merge fields; else look for DB events with same `type`/`start_date`/`end_date` and no `admin_id` → one match merges, several prompts interactively (stdin), none inserts. Manually-planned events without an admin counterpart are left untouched. Unpublished courses with zero payments are skipped.

**Module-level DB global — import order matters:** `utils/db.py` holds a global `mongo_db` set by `set_db_var()`. `vars.py` queries the DB *at import time* (building `EVENTS`, `TEACHERS`, `LOCATIONS` choices from the DB plus root `events.json`/`teachers.json`/`locations.json`), and `forms.py`/`cal.py` import it. So `set_db_var` must run before importing `cal`/`forms`/`vars` — that's why `create_app` imports blueprints after setting it. Scripts must call `set_db_var(get_db(...))` before using DB helpers. `aol_calendar/db.py` (per-request `g.db`) is currently unused.

**Legacy:** `data/*.json` and `data/manual/` are the old JSON data files from before the MongoDB migration (`scripts/copy_data_files_to_mongodb.py`); MongoDB is the source of truth now.
