# -*- coding: utf-8 -*-
"""
gate.ui
~~~~~~~

This module defines the UserInterface class. This class is responsible
for showing up the Gate user interface and to display to the user
all matching files for the given search query.
"""

import os
from collections import namedtuple
from os.path import basename, dirname, expanduser

from gate.utils import v
from gate.utils import misc
from gate.utils import input
from gate.utils import settings
from gate.exceptions import GateUnknownProfile


class UserInterface:

    def __init__(self, plug):
        self.plug = plug
        self.name = '__gate__'
        self.renderer = Renderer(plug)
        self.BufInfo = namedtuple("BufInfo", "name nr winnr")
        self._reset()

    def open(self):
        """To open the gate user interface."""
        self.user_buf = self.BufInfo(v.bufname(), v.bufnr(), v.winnr())
        prompt = u"echohl GatePrompt | echon \"{0}\" | echohl None".format(
            settings.get("prompt"))

        self._open_window()
        self._update()
        v.redraw()

        # Start the input loop
        key = input.Input()
        while True:

            self.perform_new_search = True

            # Display the prompt and the current query
            v.exe(prompt)
            query = self.query.replace(u"\\", u"\\\\").replace(u'"', u'\\"')
            v.exe(u"echon \"{0}\"".format(query))

            # Wait for the next pressed key
            key.get()

            # Go to the file on the current line
            if key.RETURN or key.CTRL and key.CHAR in ('e', 'o', 'v', 's', 't'):
                file = self.mapper.get(self.cursor_pos)

                if key.RETURN or key.CHAR in ('o', 'e'):
                    mode = 'e'
                else:
                    mode = key.CHAR

                if file:
                    self._go_to(file, mode)
                    break

            # Close the gate window
            elif key.ESC or key.INTERRUPT:
                self._close()
                break

            # Delete a character backward
            elif key.BS or key.CTRL and key.CHAR == "h":
                query = self.query.strip()
                self.query = u"{0}".format(self.query)[:-1]
                self.cursor_pos = -1  # move the cursor to the bottom

            # Move the cursor up
            elif key.UP or key.TAB or key.CTRL and key.CHAR == 'k':
                self.perform_new_search = False
                if self.cursor_pos == 0:
                    self.cursor_pos = len(v.buffer()) - 1
                else:
                    self.cursor_pos -= 1

            # Move the cursor down
            elif key.DOWN or key.CTRL and key.CHAR == 'j':
                self.perform_new_search = False
                if self.cursor_pos == len(v.buffer()) - 1:
                    self.cursor_pos = 0
                else:
                    self.cursor_pos += 1

            # Clear the current search
            elif key.CTRL and key.CHAR == 'u':
                query = self.query.lstrip()
                if len(query.split(":")) == 2:
                    profile, _ = query.split(":")
                    self.query = profile + ":"
                else:
                    self.query = ""
                self.cursor_pos = -1  # move the cursor to the bottom

            # Ban the file under cursor
            elif key.CTRL and key.CHAR == 'b':
                file = self.mapper.get(self.cursor_pos)
                if file is not None:
                    self.plug.banned.add(file["path"])
                    self.cursor_pos = -1  # move the cursor to the bottom

            # A character has been pressed.
            elif key.CHAR:
                self.query += key.CHAR
                self.cursor_pos = -1  # move the cursor to the bottom

            else:
                v.redraw()
                continue

            self._update()
            v.redraw()

    def _open_window(self):
        """To open the gate window if not already visible."""
        if not self.winnr:
            self.exit_cmds.append(u"set ei={0}".format(v.opt("ei")))
            v.exe(u"set eventignore=all")
            v.exe(u'sil! keepa botright 1new {0}'.format(self.name))
            self._setup_buffer()
            self.winnr = v.bufwinnr(self.name)

    def _close(self):
        """To close the Gate user interface."""
        v.exe('q')
        for cmd in self.exit_cmds:
            v.exe(cmd)
        if self.user_buf.winnr:
            v.focus_win(self.user_buf.winnr)
        self._reset()
        v.redraw()

    def _reset(self):
        """To reset the Gate user interface state."""
        self.user_buf = None
        self.query = u""
        self.winnr = None
        self.mapper = {}
        self.cursor_pos = -1
        self.exit_cmds = []
        self.search_results_cache = []
        self.perform_new_search = True

    def _setup_buffer(self):
        """To set sane options for the search results buffer."""
        last_search = v.eval("@/").replace(u'"', u'\\"') if v.eval("@/") else ""
        self.exit_cmds.extend([
            u"let @/=\"{0}\"".format(last_search),
            u"set laststatus={0}".format(v.opt("ls")),
            u"set guicursor={0}".format(v.opt("gcr")),
        ])

        commands = [
            "let @/ = ''",
            "call clearmatches()"
        ]

        options = [
            "buftype=nofile", "bufhidden=wipe", "nobuflisted", "noundofile",
            "nobackup", "noswapfile", "nowrap", "nonumber", "nolist",
            "textwidth=0", "colorcolumn=0", "laststatus=0", "norelativenumber",
            "nocursorcolumn", "nospell", "foldcolumn=0", "foldcolumn=0",
            "guicursor=a:hor5-Cursor-blinkwait100",
        ]

        if settings.get("cursorline", bool):
            options.append("cursorline")
        else:
            options.append("nocursorline")

        for opt in options:
            v.exe(u"try|setl {0}|catch|endtry".format(opt))

        for cmd in commands:
            v.exe(cmd)

    def _update(self):
        """To update search results."""
        try:
            matches = []
            if self.perform_new_search:
                max_results = settings.get('max_results', int)
                matches = self.plug.find(self.query, max_results, self.user_buf.name)
                self.search_results_cache = matches
            else:
                matches = self.search_results_cache
            if not matches:
                self.renderer.render_msg(" nothing found...")
            else:
                self.renderer.render_files(self.query, matches)
        except GateUnknownProfile:
            self.renderer.render_msg(" unknown search profile...")

    def _go_to(self, match, mode='e'):
        """To jump to the file on the current line."""
        self._close()
        if not v.opt("hidden", fmt=bool) and v.opt("mod", fmt=bool):
            v.echo(u"Write the buffer first. (:h hidden)", "WarningMsg")
        else:
            map = {"e": "edit", "t": "tabedit", "s": "split", "v": "vsplit"}
            v.exe(u"sil! {0} {1}".format(map[mode], match["path"].replace(u" ", u"\ ")))
            v.exe("normal! zvzzg^")


class Renderer:

    def __init__(self, plug):
        self.plug = plug

    def render_msg(self, msg, hl="None"):
        """To display a single line message to the user."""
        v.exe('syntax clear')
        v.focus_win(self.plug.ui.winnr)
        v.setbuffer(msg)
        v.setwinh(1)
        v.highlight(hl, ".*")
        self.plug.ui.cursor_pos = 0
        v.cursor((1, 0))
        v.exe("norm! 0")

    def render_files(self, query, files):
        """To render all search results."""
        v.exe('syntax clear')
        v.focus_win(self.plug.ui.winnr)
        files = files[::-1]
        self.plug.ui.mapper = dict(enumerate(f for f in files))
        v.setbuffer([self._render_line(f, query) for f in files])
        self.plug.ui.cursor_pos = self._render_curr_line(self.plug.ui.cursor_pos)
        self._highlight(files, self.plug.ui.cursor_pos)
        v.setwinh(len(files))
        v.cursor((self.plug.ui.cursor_pos + 1, 0))
        v.exe("norm! 0")

    def _render_line(self, match, query):
        """To format a single line with the file information."""
        root = self.plug.project.get_root()
        if root and match["path"].startswith(root + os.path.sep):
            fpath = match["path"].replace(dirname(root) + os.path.sep, "")
        else:
            fpath = match["path"].replace(expanduser("~"), "~")
        try:
            fmtstr = settings.get("file_path")
            fpath = fmtstr.format(**{"path": fpath})
        except KeyError:
            fpath = "<ERROR>"

        modflag = u" "
        if settings.get("mod_flag") and v.ismod(match["path"]):
            modflag = settings.get("mod_flag")

        debug = settings.get("debug", bool)
        return u"{0}{1}{2}{3}{4}".format(
            u" "*len(settings.get("curr_line_indicator")),
            basename(match["path"]), modflag, fpath,
            u" ({0:.4})".format(match["similarity"]) if debug else "")

    def _render_curr_line(self, cursor_pos):
        """To add an indicator in front of the current line."""
        if cursor_pos < 0:
            cursor_pos = len(v.buffer()) - 1
        line = v.getline(cursor_pos)
        indicator = settings.get("curr_line_indicator")
        v.setline(cursor_pos, indicator + line[len(indicator):])
        return cursor_pos

    def _highlight(self, matches, curr_line):
        """To highlight search results."""
        indicator = settings.get("curr_line_indicator")
        for i, match in enumerate(matches):
            if i == curr_line:
                offset = len(v.encode(indicator))
                patt = u"\%{0}l\%<{1}c.\%>{2}c".format(i+1, offset+1, 0)
                v.highlight("GateCurrLineIndicator", patt)
            else:
                offset = len(indicator)

            fname_byte_len = len(v.encode(basename(match["path"])))

            for pos in misc.as_byte_indexes(match["match_positions"], basename(match["path"])):
                patt = u"\%{0}l\%{1}c.".format(i+1, offset+pos+1)
                v.highlight("GateMatch", patt)

            if settings.get("mod_flag") and v.ismod(match["path"]):
                modflag_byte_len = len(v.encode(settings.get("mod_flag")))
                start = offset + fname_byte_len + 1
                end = start + modflag_byte_len
                patt = u"\%{0}l\%<{1}c.\%>{2}c".format(i+1, end, start)
                v.highlight("GateModFlag", patt)
                offset += modflag_byte_len

            fname_byte_len = len(v.encode(basename(match["path"])))
            patt = u"\%{0}l\%{1}c.*".format(i+1, offset+fname_byte_len+1)
            v.highlight("GateFilePath", patt)

