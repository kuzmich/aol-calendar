# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Calendar of Art of Living courses and events in Irkutsk. It is a Django + Postgres app (`manage.py`, `config/`, `events/`), live on serv00 at https://calendar.maxc4m.serv00.net. User-facing text, docstrings, comments and commit messages are in Russian.

## Commands

```bash
docker compose up -d                                            # Postgres 18 on 127.0.0.1:5433
uv run --env-file .env manage.py migrate
uv run --env-file .env manage.py runserver 8001                 # calendar at /<year>.html, admin at /admin/ (port 8000 is taken locally)
uv run --env-file .env manage.py test events                    # all tests
uv run --env-file .env manage.py test events.tests.GetCalBlocksTest.test_same_month_dates
uvx pyright events config                                       # type check (django-stubs in dev deps)
uv run fab deploy                                               # deploy to serv00
```

- Env vars come from `.env` (template `.env.example`): `POSTGRES_*` (defaults match `compose.yaml`), `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `AOL_ADMIN_EMAIL`/`AOL_ADMIN_PASSWORD` (artofliving.ru admin login for sync). `.env` is read only at process start, so restart `runserver` after changing it.
- The `aa` package (`aa.proxy.admin`: login and scraping of the artofliving.ru admin) is a local editable package at `../automation`. It is in the `sync` dependency group, which uv installs by default via `tool.uv.default-groups`. It's not on PyPI, so it is kept out of the calendar wheel's metadata. `uv sync` fails without the sibling checkout.
- Deployment: `uv run fab deploy` (`fabfile.py`) builds two wheels: `aa` (from `git archive HEAD` of `../automation`, so uncommitted changes there are not deployed) and the calendar (packages `config`, `events`). It installs both into `~/venvs/aol-calendar` on `ssh serv00`, runs `migrate`/`collectstatic` and restarts Passenger. `uv run fab manage --args '<django-admin command>'` runs other commands there. Server-only files live in `~/domains/calendar.maxc4m.serv00.net/public_python/`: `passenger_wsgi.py` and `settings_serv00.py` (secrets, DB, paths, `from config.settings import *`), with templates in `deploy/`. Since the version is always 0.1.0, wheels are reinstalled with `--force-reinstall --no-deps`.
- GitHub Pages (https://kuzmich.github.io/aol-calendar/) only redirects to serv00. `out/` holds hand-written redirect stubs (`index.html`, `<year>.html`, `404.html`: meta refresh + `location.replace` keeping the `#month` hash), published by `.github/workflows/static.yml` on push to `master`.

## Architecture

**Schema** (`events/models.py`): `Event` has FKs to the lookup tables `EventType` (`slug` used for CSS colors and JS filters, `name` = course name), `Place` and `Status`, plus M2M `teachers` (`Teacher` with `last_name`/`first_name`; order is not stored). `start_date`/`end_date` are `DateField`s. Times live in optional `EventDay` rows (one per day, only for days whose time is known), because multi-day courses can have different times each day. `admin_id`/`admin_link`/`public_link`/`num_payments` (number of people who paid) come from the site admin. `mongo_id` links an event to the old MongoDB document (archive dump in `dump/`, not in git).

**Calendar page:** `events/calendar.py::calendar_context(year)` loads one year of events, turns them into dicts and runs them through `events/grid.py`. There, `prepare_events` splits each event into per-week blocks clipped to the month (`get_cal_blocks`) and assigns stacking levels to overlapping blocks (`assign_levels`). The template positions blocks with CSS Grid `grid-row`/`grid-column`. `events/views.py` renders `events/jinja2/events/page.html` for `YEARS` (shown in the nav) and `ARCHIVE_YEARS` (reachable by URL only). Pages use Jinja2: the backend is set up in `config/settings.py`, and `config/jinja2.py` provides the `static`/`url` globals and the `teacher_names` filter (`events/filters.py`). The Django admin uses Django templates (`events/templates/admin/`). `can_edit` (staff users) adds links into the admin via `events/static/events/staff.js`. Russian month names and `human_dates` are in `events/dates.py`.

**Sync with the artofliving.ru admin** (`events/sync.py`, page `/admin/events/event/sync/`, button on the events changelist): courses are planned in the calendar, and a course page is created in the site admin only when needed.
- `fetch_admin_courses` loads one month via `aa.proxy.admin`. A wrong password still "logs in", but the course list then returns 403, so access to the list is checked explicitly.
- `parse_admin_course` normalizes each course. `COURSE_NAME_TYPE` maps lowercased admin names to type slugs, and unknown names can only be skipped; `EVENT_TYPE_PATH` builds `public_link`.
- `plan_sync` proposes an action per course. An event with the same `admin_id` is updated. Otherwise an event without `admin_id` with the same type and dates is merged into: same place → preselected, other place → offered but not preselected, none → create.
- Parsed courses are kept in the session between "fetch" and "apply".
- `apply_course` overwrites type/dates/place/status/teachers/num_payments/admin fields and never touches `EventDay`.

When adding a new course name, add it to `COURSE_NAME_TYPE` (and `EVENT_TYPE_PATH`, plus a CSS color in `events/static/events/calendar.css` if it is a new type).
