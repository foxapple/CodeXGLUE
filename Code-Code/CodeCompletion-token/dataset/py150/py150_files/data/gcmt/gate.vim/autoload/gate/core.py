# -*- coding: utf-8 -*-
"""
gate.core
~~~~~~~~~

This module defines the Gate class.
"""

from __future__ import division

from datetime import datetime
from operator import itemgetter
from os.path import basename, splitext
from collections import defaultdict

from gate import ui
from gate import project
from gate import session
from gate.utils import v
from gate.utils import settings
from gate.utils.match import match
from gate.exceptions import GateUnknownProfile


class Gate:

    def __init__(self):
        self.project = project.Project()
        self.session = session.Session()
        self.ui = ui.UserInterface(self)
        self.history = defaultdict(datetime.now)
        self.frequency = defaultdict(int)
        self.banned = set()

    def update_history(self):
        """To update the history for the current buffer.

        This function is called whenever the user enters a buffer.
        """
        buf = v.bufname()
        self.history[buf] = datetime.now()
        self.frequency[buf] += 1

    def open(self):
        """To open the Gate user interface."""
        self.ui.open()

    def find(self, query, max_results=-1, curr_buf=""):
        """To find all matching files for the given `query`."""
        profile, query = self._split_query(query.strip())
        if query or (not profile and not query):
            if profile:
                if profile in settings.get("profiles"):
                    files = self.project.get_files(profile, curr_buf)
                else:
                    raise GateUnknownProfile("")
            else:
                files = self.session.get_files(curr_buf)
            return self._find(query, files, max_results)
        return []

    def _split_query(self, query):
        """To extract the search profile from the query. The clean query is
        also returned."""
        if len(query.split(":")) > 1:
            return query.split(":", 1)
        return u"", query

    def _find(self, query, files, max_results):
        """To find all matching files for the given `query`."""
        smart_case = settings.get("smart_case", int)
        match_ext = settings.get("match_file_extension", int)

        def fname(f):
            if match_ext:
                return basename(f)
            else:
                return splitext(basename(f))[0]

        matches = []
        for f in (f for f in files if f not in self.banned):
            if not query:
                similarity, positions = self.history[f], (v.opt("columns", fmt=int),)
            else:
                similarity, positions = match(query, fname(f), smart_case)
                similarity *= (1 + self.frequency[f]/100)
            if positions:
                matches.append({
                    "match_positions": positions,
                    "similarity": similarity,
                    "path": f,
                })

        if max_results < 0 or max_results > len(matches):
            max_results = len(matches)

        keyfn = itemgetter("similarity")
        return sorted(matches, key=keyfn, reverse=True)[:max_results]
