from schemas.index import schema as default
from schemas.index import update_modified
from modules.validations import is_required, is_email, is_string, \
    has_min_length, is_one_of
import rethinkdb as r
from passlib.hash import bcrypt
from modules.util import extend


def encrypt_password(value):
    if value and not value.startswith('$2a$'):
        return bcrypt.encrypt(value)
    return value


def lowercase_and_strip(s):
    return s.lower().strip()


schema = extend({}, default, {
    'tablename': 'users',
    'fields': {
        'modified': {
            'default': r.now(),
            'bundle': update_modified,
            'access': ('private',),
        },
        'name': {
            'validate': (is_required, is_string,),
            'bundle': lowercase_and_strip,
            'unique': True,
        },
        'email': {
            'validate': (is_required, is_email,),
            'bundle': lowercase_and_strip,
            'unique': True,
            'access': ('private',),
        },
        'password': {
            'validate': (is_required, is_string, (has_min_length, 8)),
            'access': ('PaSsWoRd',),
            'bundle': encrypt_password,
        },
        'settings': {
            'validate': (is_required,),
            'default': {},
            'access': ('private',),
            'embed': {
                'email_frequency': {
                    'validate': (is_required, is_string, (
                        is_one_of, 'immediate', 'daily', 'weekly', 'never',
                    )),
                    'access': ('private',),
                    'default': 'daily',
                },
                'view_sets': {
                    'validate': (is_required, is_string, (
                        is_one_of, 'public', 'private'
                    )),
                    'access': ('private',),
                    'default': 'private',
                },
                'view_follows': {
                    'validate': (is_required, is_string, (
                        is_one_of, 'public', 'private'
                    )),
                    'access': ('private',),
                    'default': 'private',
                },
            }
        }
    },
    'validate': [],
})
