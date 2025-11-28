from pathlib import Path

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DB_URL='mongodb://127.0.0.1:27017/',
        DB_NAME='aol_calendar',
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    from . import db, cal, filters

    db.init_app(app)
    app.register_blueprint(cal.bp)
    app.jinja_env.filters['teacher_names'] = filters.teacher_names

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
