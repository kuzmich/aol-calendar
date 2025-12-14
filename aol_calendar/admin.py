from flask import request, redirect, url_for, render_template, abort, Blueprint
from .utils.db import mongo_db


bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route("/events/")
def events():
    db = mongo_db
    col = db['events']
    events = col.find().sort('start_date')

    return render_template(
        'admin/events.html',
        events=events
    )
