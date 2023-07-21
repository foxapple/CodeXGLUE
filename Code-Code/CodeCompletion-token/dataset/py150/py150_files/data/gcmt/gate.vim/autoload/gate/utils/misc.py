# -*- coding: utf-8 -*-
"""
gate.utils.misc
~~~~~~~~~~~~~~~

This module defines some utility functions.
"""

from gate.utils import v
from fnmatch import fnmatch as _fnmatch


def fnmatch(fname, patterns):
    """Augmented `fnmatch`.

    When a list of patterns is given, consider the match successful when any of
    the patterns matches with `fname`.
    """
    if isinstance(patterns, list):
        return any(_fnmatch(fname, patt) for patt in patterns)
    if isinstance(patterns, basestring):
        return _fnmatch(fname, patterns)


def as_byte_indexes(indexes, s):
    """To transform character indexes into byte indexes."""
    idx = 0
    byte_indexes = []
    for i, c in enumerate(s):
        if i in indexes:
            byte_indexes.append(idx)
        idx += len(v.encode(c))
    return byte_indexes
