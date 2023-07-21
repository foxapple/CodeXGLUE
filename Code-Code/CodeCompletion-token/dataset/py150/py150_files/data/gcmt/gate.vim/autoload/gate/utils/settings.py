# -*- coding: utf-8 -*-
"""
gate.utils.settings
~~~~~~~~~~~~~~~~~~~

This module defines various utility functions for retrieving Gate options.
"""

from gate.utils import v


prefix = 'g:gate_'


def get(name, fmt=None):
    """To get the value of a vim variable."""
    if not v.eval(u"exists('{0}')".format(prefix + name), fmt=bool):
        raise ValueError("Option '{0}' does not exists".format(prefix + name))
    return v.eval(prefix + name, fmt=fmt)
