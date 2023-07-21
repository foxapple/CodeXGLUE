import logging
from datetime import datetime

from aleph.core import db, url_for
from aleph.model.role import Role
from aleph.model.schema_model import SchemaModel
from aleph.model.common import SoftDeleteModel, IdModel

log = logging.getLogger(__name__)


class Collection(db.Model, IdModel, SoftDeleteModel, SchemaModel):
    _schema = 'collection.json#'

    label = db.Column(db.Unicode)
    foreign_id = db.Column(db.Unicode, unique=True, nullable=False)

    creator_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)
    creator = db.relationship(Role)

    def update(self, data):
        self.schema_update(data)

    def delete(self):
        for entity in self.entities:
            entity.delete()
        super(Collection, self).delete()

    def touch(self):
        self.updated_at = datetime.utcnow()
        db.session.add(self)

    @classmethod
    def by_foreign_id(cls, foreign_id, data, role=None):
        q = cls.all().filter(cls.foreign_id == foreign_id)
        collection = q.first()
        if collection is None:
            collection = cls.create(data, role)
            collection.foreign_id = foreign_id
        collection.update(data)
        db.session.add(collection)
        db.session.flush()
        return collection

    @classmethod
    def create(cls, data, role):
        collection = cls()
        collection.update(data)
        collection.creator = role
        db.session.add(collection)
        return collection

    @classmethod
    def timestamps(cls):
        q = db.session.query(cls.id, cls.updated_at)
        q = q.filter(cls.deleted_at == None)  # noqa
        return q.all()

    def __repr__(self):
        return '<Collection(%r, %r)>' % (self.id, self.label)

    def __unicode__(self):
        return self.label

    def to_dict(self):
        data = super(Collection, self).to_dict()
        data['api_url'] = url_for('collections_api.view', id=self.id)
        data['foreign_id'] = self.foreign_id
        data['creator_id'] = self.creator_id
        return data
