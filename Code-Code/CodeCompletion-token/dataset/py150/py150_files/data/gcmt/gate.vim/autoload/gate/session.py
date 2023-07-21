# -*- coding: utf-8 -*-
"""
gate.session
~~~~~~~~~~~~

This module defines the Project class. This class represents the
current session, from the user perspective.
"""

from fnmatch import fnmatch
from itertools import ifilter

from gate.utils import v
from gate.utils import settings
from gate.utils.misc import fnmatch


class Session:

    def __init__(self):
        self.files = []
        self._setup_cache_rules()

    def _setup_cache_rules(self):
        """To set up rules for when the cache needs to be updated."""
        v.exe("augroup gate_session")
        v.exe("au!")
        v.exe("au BufDelete,BufNew * if empty(&bt) | exec 'py _gate.session.files = []' | end")
        v.exe("augroup END")

    def get_files(self, curr_buf):
        """To get all open files in the current vim session."""
        if not self.files:
            ignored = lambda f: fnmatch(f, settings.get("ignore"))
            self.files = [f for f in v.buffers() if not ignored(f)]
        return ifilter(lambda f: f != curr_buf, self.files)
