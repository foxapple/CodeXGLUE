"""
    polaris.utils
    ~~~~~~~~~~~~~

    :copyright: (c) 2013 Eleme, http://polaris.eleme.io
    :license: MIT
"""

import re
import hashlib
import string

# regex pattern from wtforms
_email_regex = re.compile(r'^.+@([^.@][^@]+)$')


def kw_generator(namespace, fn, **kw):
    fname = fn.__name__

    def generate_key(*arg, **kw):
        args_str = ",".join([str(s) for s in arg] +
                            ["{}={}".format(k, kw[k]) for k in sorted(kw)])
        hashed_str = hashlib.md5(args_str.encode("utf-8")).hexdigest()
        return "{}_{}|{}".format(namespace, fname, hashed_str)
    return generate_key


def sanitize_string(s, extra_chars=''):
    chars = string.ascii_letters + string.digits + extra_chars
    return ''.join([c for c in s if c in chars])


def validate_email(s):
    if _email_regex.match(s):
        return True
    return False
