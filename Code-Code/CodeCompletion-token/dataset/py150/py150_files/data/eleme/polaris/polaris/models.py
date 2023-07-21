import datetime
import json
import uuid

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.http import http_date

from polaris.utils import sanitize_string, validate_email


##########
# Models
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "pl_user"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String, nullable=False, unique=True)
    nickname = db.Column(db.String, default='', nullable=False)
    _password = db.Column("password", db.String, nullable=False)
    is_valid = db.Column(db.Boolean, default=False, nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)

    # foreign key ref
    charts = db.relationship("Chart", lazy="dynamic",
                             order_by="desc(Chart.stars)")
    chartstars = db.relationship("ChartStar", backref="user", lazy="dynamic")

    dashboards = db.relationship("Dashboard", lazy="dynamic",
                                 order_by="desc(Dashboard.stars)")
    dashboardstars = db.relationship("DashboardStar",
                                     backref="user", lazy="dynamic")

    groups = db.relationship("GroupMember", backref="user", lazy="joined",
                             order_by="GroupMember.is_admin")
    oauthusers = db.relationship("OauthUser", backref="user", lazy="dynamic")

    # for flask-login
    is_authenticated = lambda self: True
    is_active = lambda self: self.is_valid
    is_anonymous = lambda self: False
    get_id = lambda self: self.id

    def __init__(self, email, username, password, nickname=''):
        """Only allow some fields to be set in init.
        """
        self.email = email
        self.username = username
        self.password = password
        self.nickname = nickname

    def __repr__(self):
        return "<User(id={}, email={})>".format(self.id, self.email)

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pwd):
        self._password = generate_password_hash(pwd)

    def auth(self, pwd):
        return check_password_hash(self.password, pwd)

    @db.validates('username', include_removes=True)
    def validate_username(self, key, username, is_remove):
        if is_remove:
            raise ValueError("Not allowed to remove username")
        return sanitize_string(username, extra_chars='.')

    @db.validates('email', include_removes=True)
    def validate_email(self, key, email, is_remove):
        if is_remove:
            raise ValueError("Not allowed to remove eamil")

        assert validate_email(email)
        assert sanitize_string(email, extra_chars='.@') == email
        return email

    def to_dict(self):
        return {
            "id": str(self.id), "email": self.email, "username": self.username,
            "nickname": self.nickname, "is_valid": self.is_valid,
            "is_superadmin": self.is_superadmin,
            "created_at": http_date(self.created_at),
            "charts": [c.to_dict() for c in self.charts],
            "dashboards": [d.to_dict() for d in self.dashboards]
        }


class OauthUser(db.Model):
    __tablename__ = "pl_oauthuser"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.UUID, db.ForeignKey('pl_user.id'), nullable=False)
    provider_id = db.Column(db.String, nullable=False)
    provider_email = db.Column(db.String, nullable=False)
    provider_info = db.Column(db.JSON, nullable=False)
    provider = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)


class Group(db.Model):
    __tablename__ = "pl_group"

    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    slug = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)

    charts = db.relationship("Chart", lazy="dynamic",
                             order_by="desc(Chart.stars)")
    dashboards = db.relationship("Dashboard", lazy="dynamic",
                                 order_by="desc(Dashboard.stars)")
    members = db.relationship("GroupMember", backref="group", lazy="dynamic",
                              order_by="desc(GroupMember.created_at)")

    def __init__(self, slug, name):
        assert current_user.is_authenticated()

        self.slug = slug
        self.name = name
        self.members.append(GroupMember(user_id=current_user.id,
                                        is_admin=True))

    def add_member(self, member):
        self.members.append(member)

    def is_member(self, user):
        return bool(self.members.filter(GroupMember.user_id == user.id).
                    first())

    def is_admin(self, user):
        return bool(self.members.
                    filter(GroupMember.user_id == user.id).
                    filter(GroupMember.is_admin).
                    first())

    def to_dict(self):
        return {"id": str(self.id), "slug": self.slug, "name": self.name,
                "created_at": http_date(self.created_at)}


class GroupMember(db.Model):
    __tablename__ = "pl_groupmember"

    group_id = db.Column(db.UUID, db.ForeignKey('pl_group.id'),
                         primary_key=True)
    user_id = db.Column(db.UUID, db.ForeignKey('pl_user.id'),
                        primary_key=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)


class Chart(db.Model):
    """Chart model.

    Chart may belong to user or group. User can star and fork chart.
    """
    __tablename__ = "pl_chart"

    # column definitions
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False, default="")
    category = db.Column(db.String, nullable=False, default="basic")
    source = db.Column(db.String, nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.UUID, db.ForeignKey('pl_user.id'))
    group_id = db.Column(db.UUID, db.ForeignKey('pl_group.id'))
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    stars = db.Column(db.Integer, default=0, nullable=False)
    fork_id = db.Column(db.UUID, db.ForeignKey('pl_chart.id'))
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)

    user = db.relationship("User", lazy="joined")
    group = db.relationship("Group", lazy="joined")
    parent = db.relationship("Chart", remote_side=id)
    children = db.relationship("Chart", remote_side=fork_id, lazy="dynamic")

    starred_users = db.relationship("ChartStar", backref="chart",
                                    lazy="dynamic")

    def __init__(self, **kwargs):
        assert current_user.is_authenticated()

        for f in ("name", "description", "source", "payload", "fork_id",
                  "group_id", "is_public"):
            if kwargs.get(f) is not None:
                setattr(self, f, kwargs[f])

        self.category = current_app.config["category"][self.source]

        if not self.group_id:
            self.user_id = current_user.id

    def __repr__(self):
        return "Chart({})".format(str(self))

    def __str__(self):
        return json.dumps(self.to_dict())

    @property
    def username(self):
        return self.user.username if self.user_id else ""

    @property
    def nickname(self):
        return self.user.nickname if self.user_id else ''

    @property
    def groupname(self):
        return self.group.name if self.group_id else ""

    @property
    def short(self):
        if self.user_id:
            return self.username + '/' + self.slug
        elif self.group_id:
            return self.groupname + '/' + self.slug

    def to_dict(self):
        res = {}
        uuids = ("id", "fork_id", "user_id", "group_id")
        for u in uuids:
            val = getattr(self, u)
            res[u] = str(val) if val else ''

        fields = ("name", "description", "category", "source", "payload",
                  "username", "nickname", "groupname", "is_public", "stars")
        res.update({f: getattr(self, f) for f in fields})
        res["created_at"] = http_date(self.created_at)
        return res

    @db.validates('slug', include_removes=True)
    def validate_slug(self, key, slug, is_remove):
        if is_remove:
            raise ValueError("Not allowed to remove slug")
        return sanitize_string(slug, extra_chars='_')

    @db.validates('category')
    def validate_category(self, key, category):
        assert category in ('basic', 'map')
        return category


class Dashboard(db.Model):
    """Dashboard model.

    Dashboard may belong to user or group. User can star but can't fork
    dashboard.
    """
    __tablename__ = "pl_dashboard"

    # column definitions
    id = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    slug = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False, default="")
    payload = db.Column(db.JSON, nullable=False)
    user_id = db.Column(db.UUID, db.ForeignKey('pl_user.id'))
    group_id = db.Column(db.UUID, db.ForeignKey('pl_group.id'))
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    stars = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)

    user = db.relationship("User", lazy="joined")
    group = db.relationship("Group", lazy="joined")

    starred_users = db.relationship("DashboardStar", backref="dashboard",
                                    lazy="dynamic")

    def __init__(self, **kwargs):
        assert current_user.is_authenticated()

        for f in ("slug", "name", "description", "payload",
                  "user_id", "group_id", "is_public"):
            if kwargs.get(f) is not None:
                setattr(self, f, kwargs[f])

        if not self.group_id:
            self.user_id = current_user.id

    def __repr__(self):
        return "Dashboard({})".format(str(self))

    def __str__(self):
        return json.dumps(self.to_dict())

    @property
    def username(self):
        return self.user.username if self.user_id else ""

    @property
    def nickname(self):
        return self.user.nickname if self.user_id else ''

    @property
    def groupname(self):
        return self.group.name if self.group_id else ""

    @property
    def short(self):
        return '/'.join([self.username, self.slug])

    def to_dict(self):
        res = {}
        uuids = ("id", "user_id", "group_id")
        for u in uuids:
            val = getattr(self, u)
            res[u] = str(val) if val else ''

        fields = ("slug", "name", "description", "payload", "short",
                  "username", "nickname", "groupname", "is_public", "stars")
        res.update({f: getattr(self, f) for f in fields})
        res["created_at"] = http_date(self.created_at)
        return res

    @db.validates('slug', include_removes=True)
    def validate_slug(self, key, slug, is_remove):
        if is_remove:
            raise ValueError("Not allowed to remove slug")
        return sanitize_string(slug, extra_chars='_')


class ChartStar(db.Model):
    """Chart User star association mapping.
    """
    __tablename__ = "pl_chartstar"

    user_id = db.Column(db.UUID, db.ForeignKey('pl_user.id'),
                        primary_key=True)
    chart_id = db.Column(db.UUID, db.ForeignKey('pl_chart.id'),
                         primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)


class DashboardStar(db.Model):
    """Dashboard User star association mapping.
    """
    __tablename__ = "pl_dashboardstar"

    user_id = db.Column(db.UUID, db.ForeignKey('pl_user.id'),
                        primary_key=True)
    dashboard_id = db.Column(db.UUID, db.ForeignKey('pl_dashboard.id'),
                             primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=datetime.datetime.now,
                           nullable=False)
