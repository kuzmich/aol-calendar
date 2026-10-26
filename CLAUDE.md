# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Calendar of Art of Living courses and events in Irkutsk. The live site is the Django app on serv00 (https://calendar.maxc4m.serv00.net) backed by Postgres. User-facing text, docstrings, comments and commit messages are in Russian.

The project is migrating from Flask + MongoDB to Django + Postgres. The Django side (`manage.py`, `config/`, `events/`) provides the Django admin and the calendar page. The legacy Flask/MongoDB code (`aol_calendar/`, `scripts/`) still exists; Django reuses some of its utilities.

## Commands

```bash
docker compose up -d                                            # MongoDB 8.2 on 127.0.0.1:27017, Postgres 18 on 127.0.0.1:5433
uv run --env-file .env manage.py migrate
uv run --env-file .env manage.py import_mongo                   # copy Mongo events → Postgres (idempotent, by mongo_id)
uv run --env-file .env manage.py runserver 8001                 # calendar at /<year>.html, admin at /admin/ (port 8000 is taken locally)
uv run --env-file .env manage.py test events                    # Django tests (pytest only covers tests/)
uv run --env-file .env flask --app aol_calendar run --debug     # editing site (Flask)
uv run --env-file .env scripts/make_calendar.py                 # legacy: DO NOT run, it overwrites the redirect stubs in out/
uv run --env-file .env scripts/sync_events.py <year> <month>    # legacy Mongo sync; use the Django admin sync page instead
uv run pytest                                                   # tests
uv run pytest tests/test_cal_utils.py::TestGetCalBlocks::test_same_month_dates
```

- `.env` sets `AOL_CALENDAR_CONFIG`, the path to a Python config module (`instance/config.py`) with `DB_URL`, `DB_NAME`, `EMAIL`, `PASSWORD`. Scripts load it via `aol_calendar.utils.get_config()`; the Flask app reads the same `instance/config.py` via `from_pyfile`.
- The `aa` dependency is a local editable package at `../automation` (provides `aa.proxy.admin` login/scraping for the artofliving.ru admin). It lives in the `sync` dependency group (installed locally by default via `tool.uv.default-groups`, kept out of the wheel); `uv sync` fails without that sibling checkout.
- GitHub Pages (https://kuzmich.github.io/aol-calendar/) only redirects to serv00. `out/` holds hand-written redirect stubs (`index.html`, `<year>.html`, `404.html`: meta refresh + `location.replace` keeping the `#month` hash), published by `.github/workflows/static.yml` on push to `master`.
- Django deployment (serv00, https://calendar.maxc4m.serv00.net): `uv run fab deploy` builds the wheels of `aa` (from `git archive HEAD` of `../automation`, so uncommitted changes there are not deployed) and of the calendar (packages `aol_calendar`, `config`, `events`), installs them into `~/venvs/aol-calendar` on `ssh serv00`, runs `migrate`/`collectstatic` and restarts Passenger. `uv run fab manage --args '<django-admin command>'` runs other commands there. Server-only files live in `~/domains/calendar.maxc4m.serv00.net/public_python/`: `passenger_wsgi.py` and `settings_serv00.py` (secrets, DB, paths), with templates in `deploy/`. Since the version is always 0.1.0, the wheel is reinstalled with `--force-reinstall --no-deps`.

## Architecture

**Django schema** (`events/models.py`): `Event` has FKs to the lookup tables `EventType` (`slug` = the old Mongo `type`, `name` = course name), `Place` and `Status`, plus M2M `teachers` (`Teacher` with `last_name`/`first_name`). `start_date`/`end_date` are `DateField`s; the old `dates` string is dropped. Times live in optional `EventDay` rows (one per day, only for days whose time is known), because multi-day courses can have different times each day. `admin_id`/`admin_link`/`public_link`/`num_payments` (number of people who paid) come from the site admin. `mongo_id` links back to the Mongo document for re-imports. Postgres settings come from `POSTGRES_*` env vars, with defaults matching `compose.yaml`.

**Django calendar:** `events/calendar.py::calendar_context(year)` turns events into the dicts the old pipeline expects and reuses `aol_calendar/utils/cal.py` (`get_month_dates`, `prepare_events`). The view (`events/views.py`) renders `events/jinja2/events/page.html` for `YEARS` (shown in the nav) and `ARCHIVE_YEARS` (reachable by URL only). Pages use Jinja2: the backend is configured in `config/settings.py`, and `config/jinja2.py` provides the `static`/`url` globals and the `teacher_names` filter. The Django admin uses Django templates. `can_edit` (staff users) adds links into the admin via `events/static/events/staff.js`. `calendar.css`/`calendar.js` are shared from `aol_calendar/static` via `STATICFILES_DIRS`.

**Sync with the artofliving.ru admin** (`events/sync.py`, page `/admin/events/event/sync/`, button on the events changelist): courses are planned in the calendar, and a course page is created in the site admin only when needed. The page fetches one month via `aa.proxy.admin` (`log_in` + `find_courses`, credentials in `AOL_ADMIN_EMAIL`/`AOL_ADMIN_PASSWORD`), parses it (`parse_admin_course`: `COURSE_NAME_TYPE` maps names to type slugs, unknown names can only be skipped), and proposes an action per course (`plan_sync`). An event with the same `admin_id` is updated. Otherwise an event without `admin_id` with the same type and dates is merged into: same place → preselected, other place → offered but not preselected, none → create. Parsed courses are kept in the session between "fetch" and "apply". `apply_course` overwrites type/dates/place/status/teachers/num_payments/admin fields and never touches `EventDay`.

The sections below describe the legacy Flask/Mongo system.

**Data flow:** artofliving.ru admin → `sync_events.py` (`utils/admin.AdminCourses` fetches, `utils/parsing.parse_admin_event` normalizes) → MongoDB `events` collection ← Flask form (`cal.py` add/edit/delete). Then `make_calendar.py` and the Flask `/<year>.html` route both render `templates/page.html` from the DB using the same pipeline.

**Rendering pipeline** (`utils/cal.py`): for each month, `get_events(year, month)` returns events whose start *or* end falls in the month → `prepare_events` splits each event into per-week blocks (`get_cal_blocks`, clipped to the month) and assigns stacking `level`s for overlapping events (`assign_levels`). The template positions blocks with CSS Grid `grid-row`/`grid-column`, stacking levels via margin. Flask passes `can_edit=True` (edit form/dialog); the static generator doesn't, so the public pages are read-only.

**Course types:** every event has a `type` slug used for colors (CSS) and filters (JS). `const.COURSE_NAME_TYPE` maps lowercased admin course names → type; unknown names log a warning and become `unknown`. When adding a new course name, add it there (and `EVENT_TYPE_PATH` for the public link, plus CSS color if needed). Each name should map to exactly one type. `docs/FORMAT.md` documents the DB, form, and legacy data-file formats.

**Sync merge logic** (`scripts/sync_events.py`): match by `admin_id` → merge fields; else look for DB events with same `type`/`start_date`/`end_date` and no `admin_id` → one match merges, several prompts interactively (stdin), none inserts. Manually-planned events without an admin counterpart are left untouched. Unpublished courses with zero payments are skipped.

**Module-level DB global — import order matters:** `utils/db.py` holds a global `mongo_db` set by `set_db_var()`. `vars.py` queries the DB *at import time* (building `EVENTS`, `TEACHERS`, `LOCATIONS` choices from the DB plus root `events.json`/`teachers.json`/`locations.json`), and `forms.py`/`cal.py` import it. So `set_db_var` must run before importing `cal`/`forms`/`vars` — that's why `create_app` imports blueprints after setting it. Scripts must call `set_db_var(get_db(...))` before using DB helpers. `aol_calendar/db.py` (per-request `g.db`) is currently unused.

**Legacy:** `data/*.json` and `data/manual/` are the old JSON data files from before the MongoDB migration (`scripts/copy_data_files_to_mongodb.py`); MongoDB is the source of truth now.
