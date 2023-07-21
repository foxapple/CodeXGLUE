"""
    polaris.views.profile
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT

    Polaris profile based explore.
"""

import http.client as http

from flask import (
    session,
    Blueprint,
    abort,
    current_app,
    render_template,
)

from flask_login import current_user, login_required

from polaris.models import db, User, Chart, Dashboard, Group, GroupMember
from polaris.auth.principal import can_view_chart, can_view_dashboard


profile = Blueprint("profile", __name__)


@profile.route("/<string:username>")
@login_required
def dashboard_library(username=None):
    """Return user dashboard library page.
    """
    if username is None or username == current_user.username:
        user = current_user
    else:
        user = db.session.query(User).filter(User.username == username).first()
        if not user:
            abort(http.NOT_FOUND)

    session.pop(current_user.username, None)

    return render_template("library.jinja", name=user.username)


@profile.route("/explore")
@login_required
def explore():
    session.pop(current_user.username, None)

    return render_template("library.jinja", name="explore")


@profile.route("/group/new")
@login_required
def new_group():
    """Create a new group
    """
    return render_template("group_new.jinja")


@profile.route("/group/<string:group_id>")
@login_required
def group_library(group_id):
    """Return group library page.
    """
    group = db.session.query(Group).filter(Group.id == group_id).first()
    if not group:
        abort(http.NOT_FOUND)

    group.is_group_member = group.is_member(current_user)
    group.is_admin_member = group.is_admin(current_user)

    session[current_user.username] = {"name": group.name, "id": str(group.id),
                                      "admin": group.is_admin_member}

    return render_template("group_library.jinja", group=group)


@profile.route("/settings")
@login_required
def user_settings():
    return render_template("user_settings.jinja")


@profile.route("/group/settings/<string:group_id>")
@login_required
def group_settings(group_id):
    group = db.session.query(Group).filter(Group.id == group_id).first()
    if not group:
        abort(http.NOT_FOUND)

    group_member = db.session.query(GroupMember).\
        filter(GroupMember.group_id == group.id).\
        filter(GroupMember.user_id == current_user.id).\
        first()
    if not group_member or not group_member.is_admin:
        abort(http.NOT_FOUND)

    admins, members = [], []
    for m in group.members:
        if m.is_admin:
            admins.append(m.user.username)
        else:
            members.append(m.user.username)

    group_info = {
        "id": str(group.id),
        "user": str(current_user.id),
        "name": group.name
    }
    group.is_admin_member = True
    return render_template("group_settings.jinja", admins=admins,
                           members=members, group_info=group_info, group=group)


@profile.route("/<string:username>/chart/<string:uuid>")
@login_required
def chart_view(username, uuid):
    """Return dashboard view.
    """
    chart = db.session.query(Chart).get(uuid)
    if not chart or chart.user.username != username or \
            not can_view_chart(uuid):
        abort(http.NOT_FOUND)
    return render_template("chart_view.jinja",
                           mapbox_id=current_app.config["MAPBOX_ID"],
                           map_type=current_app.config["MAP_TYPE"],
                           user=current_user,
                           chart=chart)


@profile.route("/<string:username>/<string:slug>")
@login_required
def dashboard_view(username, slug):
    """Return dashboard view.
    """
    user = db.session.query(User).filter(User.username == username).first()
    if not user:
        abort(http.NOT_FOUND)
    dashboard = db.session.query(Dashboard).\
        filter(Dashboard.user_id == user.id).\
        filter(Dashboard.slug == slug).\
        first()
    if not dashboard or not can_view_dashboard(dashboard.id):
        abort(http.NOT_FOUND)
    return render_template("dashboard_view.jinja",
                           mapbox_id=current_app.config["MAPBOX_ID"],
                           map_type=current_app.config["MAP_TYPE"],
                           user=current_user,
                           uuid=dashboard.id)
