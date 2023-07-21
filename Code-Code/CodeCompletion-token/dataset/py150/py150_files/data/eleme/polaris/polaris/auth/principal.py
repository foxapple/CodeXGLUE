from flask_login import current_user

from polaris.exc import OwnerNotSetError
from polaris.models import db, Chart, Dashboard, Group, GroupMember


def can_view_chart(chart_uuid):
    chart = db.session.query(Chart).get(chart_uuid)
    if not chart:
        return False

    if current_user.is_superadmin or chart.is_public:
        return True

    if chart.user_id:
        # test user permission
        return chart.user_id == current_user.get_id()

    elif chart.group_id:
        # test group permission
        gm = db.session.query(GroupMember).\
            filter(GroupMember.user_id == current_user.get_id()).\
            filter(GroupMember.group_id == chart.group_id).\
            first()
        return bool(gm)

    else:
        raise OwnerNotSetError("chart %s don't have a owner" % chart_uuid)


def can_edit_chart(chart_uuid):
    chart = db.session.query(Chart).get(chart_uuid)
    if not chart:
        return False

    # superadmin can edit
    if current_user.is_superadmin:
        return True

    if chart.user_id:
        # test user permission, owner can edit
        return chart.user_id == current_user.get_id()

    elif chart.group_id:
        # test group permission, group admin can edit
        gm = db.session.query(GroupMember).\
            filter(GroupMember.user_id == current_user.get_id()).\
            filter(GroupMember.group_id == chart.group_id).\
            filter(GroupMember.is_admin).\
            first()
        return bool(gm)

    else:
        raise OwnerNotSetError("chart %s don't have a owner" % chart_uuid)


def can_view_dashboard(dashboard_uuid):
    dashboard = db.session.query(Dashboard).get(dashboard_uuid)
    if not dashboard:
        return False

    if current_user.is_superadmin or dashboard.is_public:
        return True

    if dashboard.user_id:
        # test user permission
        return dashboard.user_id == current_user.get_id()

    elif dashboard.group_id:
        # test group permission
        gm = db.session.query(GroupMember).\
            filter(GroupMember.user_id == current_user.get_id()).\
            filter(GroupMember.group_id == dashboard.group_id).\
            first()
        return bool(gm)

    else:
        raise OwnerNotSetError(
            "dashboard %s don't have a owner" % dashboard.id)


def can_edit_dashboard(dashboard_uuid):
    dashboard = db.session.query(Dashboard).get(dashboard_uuid)
    if not dashboard:
        return False

    # superadmin can edit
    if current_user.is_superadmin:
        return True

    if dashboard.user_id:
        # test user permission, owner can edit
        return dashboard.user_id == current_user.get_id()

    elif dashboard.group_id:
        # test group permission, group admin can edit
        gm = db.session.query(GroupMember).\
            filter(GroupMember.user_id == current_user.get_id()).\
            filter(GroupMember.group_id == dashboard.group_id).\
            filter(GroupMember.is_admin).\
            first()
        return bool(gm)

    else:
        raise OwnerNotSetError(
            "dashboard %s don't have a owner" % dashboard.id)


def can_view_group(group_uuid):
    group = db.session.query(Group).get(group_uuid)
    return bool(group)


def can_edit_group(group_uuid):
    group = db.session.query(Group).get(group_uuid)
    if not group:
        return False

    if current_user.is_superadmin:
        return True

    gm = db.session.query(GroupMember).\
        filter(GroupMember.user_id == current_user.get_id()).\
        filter(GroupMember.group_id == group_uuid).\
        filter(GroupMember.is_admin).\
        first()
    return bool(gm)
