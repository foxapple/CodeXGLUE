"""
    polaris.views.chart
    ~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    Polaris charts.
"""

import http.client as http

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
)

from flask_login import login_required, current_user

from polaris.models import db, Chart, ChartStar
from polaris.auth.principal import can_edit_chart

chart = Blueprint("chart", __name__, url_prefix="/chart")


@chart.route("/<string:uuid>", methods=["GET"])
@login_required
def view(uuid):
    """Return chart view.
    """
    chart = db.session.query(Chart).get(uuid)
    if not chart:
        abort(http.NOT_FOUND)

    chart.is_starred = db.session.query(db.func.count(ChartStar.created_at)).\
        filter(ChartStar.user_id == current_user.id).\
        filter(ChartStar.chart_id == uuid).\
        scalar()
    return render_template("chart_view.jinja",
                           mapbox_id=current_app.config["MAPBOX_ID"],
                           map_type=current_app.config["MAP_TYPE"],
                           chart=chart)


@chart.route("/new", methods=["GET"])
@chart.route("/edit/<string:chart_id>", methods=["GET"])
@login_required
def new_or_edit(chart_id=None):
    """Edit or create new chart.
    """
    if not chart_id:
        return render_template("chart_edit.jinja",
                               sources=list(current_app.config["source"]))

    else:
        if not can_edit_chart(chart_id):
            abort(http.FORBIDDEN)
        return render_template("chart_edit.jinja", chart_id=chart_id)
