from modules.model import Model
from modules.validations import is_required, is_string, is_one_of, \
    has_min_length
from framework.elasticsearch import es
from modules.util import json_prep


class Post(Model):
    """A discussion post."""
    tablename = 'posts'

    schema = dict(Model.schema.copy(), **{
        'user_id': {  # TODO-2 validate foreign
            'validate': (is_required, is_string,)
        },
        'topic_id': {
            'validate': (is_required, is_string,)
        },
        'body': {
            'validate': (is_required, is_string, (has_min_length, 1),)
        },
        'kind': {
            'validate': (is_required, is_string,
                         (is_one_of, 'post', 'proposal', 'vote')),
            'default': 'post'
        },
        'replies_to_id': {
            'validate': (is_string,)
        }
    })

    def validate(self, db_conn):
        errors = super().validate(db_conn)
        if not errors:
            errors += self.is_valid_topic_id()
        if not errors:
            errors += self.is_valid_reply(db_conn)
        return errors

    def is_valid_topic_id(self):
        """
        TODO-3 Ensure the topic is valid.
               Is there a way to allow for 'in memory only' topic?
        (We're currently validating this in the route for now...)
        """

        return []

    def is_valid_reply(self, db_conn):
        """
        A reply must belong to the same topic.
        - A post can reply to a post, proposal, or vote.
        - A proposal can reply to a post, proposal, or vote.
        - A vote may only reply to a proposal.
        """

        if self.data.get('replies_to_id'):
            query = (self.table
                         .get(self['replies_to_id']))
            post_data = query.run(db_conn)
            if not post_data:
                return [{'message': 'Replying to a non-existant post.'}]
            if post_data['topic_id'] != self['topic_id']:
                return [{'message': 'A reply must be in the same topic.'}]
        return []

    def save(self, db_conn):
        """
        Overwrite save method to add to Elasticsearch.
        """

        # TODO-2 should we validate the save worked before going to ES?

        from models.topic import Topic
        from models.user import User

        data = json_prep(self.deliver())
        topic = Topic.get(db_conn, id=self['topic_id'])
        if topic:
            data['topic'] = json_prep(topic.deliver())
        user = User.get(db_conn, id=self['user_id'])
        if user:
            data['user'] = json_prep(user.deliver())

        es.index(
            index='entity',
            doc_type='post',
            body=data,
            id=self['id'],
        )
        return super().save(db_conn)
