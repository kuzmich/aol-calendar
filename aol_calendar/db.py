from flask import current_app, g
from .utils.db import get_db as get_mongo_db


def get_db():
    if 'db' not in g:
        g.db = get_mongo_db(
            current_app.config['DB_URL'],
            current_app.config['DB_NAME']
        )
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.client.close()


def init_app(app):
    app.teardown_appcontext(close_db)
