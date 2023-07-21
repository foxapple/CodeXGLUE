"""
Copyright (c) 2013 Samuel B. Fries

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sublime
import sublime_plugin

"""
    Commands that manipulate textual data
"""

"""
    Sorts the selected text
"""


class SortTextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        regions = view.sel()

        if len(regions) < 2:
            return

        text = [view.substr(region) for region in regions]
        text.sort()

        offset = 0

        for region, textval in zip(regions, text):

            newlen = len(textval)
            oldlen = region.size()

            new_offset = newlen - oldlen

            newregion = sublime.Region(region.a + offset, region.b + offset)

            offset += new_offset

            view.replace(edit, newregion, textval)

"""
    Removes duplicate lines of text, per selection.
"""


class RemoveDuplicateLinesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        regions = view.sel()

        for region in regions:
            line_regions = view.split_by_newlines(region)
            seen = set()
            result = []
            for line in line_regions:
                value = view.substr(line)
                if value not in seen:
                    seen.add(value)
                    result.append(value)

            view.replace(edit, region, "\n".join(result))


"""
    Shifts selected text left
"""


class ShiftSelectionsLeftCommand   (sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        regions = view.sel()

        new_regions = []

        for region in regions:

            if (region.begin() == 0):
                new_regions.append(region)
                continue

            text = view.substr(region)
            view.erase(edit, region)
            view.insert(edit, region.begin() - 1, text)
            new_regions.append(sublime.Region(region.begin() - 1, region.end() - 1))

        view.sel().clear()

        for sel in new_regions:
            view.sel().add(sel)


"""
    Shifts selected text right
"""


class ShiftSelectionsRightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        regions = view.sel()

        new_regions = []

        for region in regions:
            #Skip regions that will move outside the bounds of the file
            if (region.end() + 1 > view.size()):
                new_regions.append(region)
                continue

            text = view.substr(region)

            view.erase(edit, region)
            view.insert(edit, region.begin() + 1, text)
            new_regions.append(sublime.Region(region.begin() + 1, region.end() + 1))

        view.sel().clear()

        for sel in new_regions:
            view.sel().add(sel)


"""
    Splits selected text into lines of a specified maximum length, breaking at words.
"""


class LineLengthCommand(sublime_plugin.TextCommand):

    def receive_input(self, length):
        view = self.view
        sel = view.sel()

        try:
            length = int(length)
        except ValueError:
            view.message_dialog("Please enter a numeric line length; %s is not an integer." % length)
            return

        for selected in sel:

            sub = view.substr(selected)

            sub_words = sub.split()

            #Each string in here will become a line
            lines = [""]
            for word in sub_words:
                if len(lines[-1]) + len(word) > length:
                    lines.append(word)
                else:
                    lines[-1] = "%s %s" % (lines[-1], word)
            #This doesn't appear to be working in ST3.  
            #Data's all fine up to this point, but 
            #it's not changing the value at all.
            print(self.edit)
            view.replace(self.edit, selected, "\n".join(lines))

    def run(self, edit):
        self.edit = edit
        self.view.window().show_input_panel("Max Line Length", "", self.receive_input, None, None)
