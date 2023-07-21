import sublime, sublime_plugin
import subprocess
import webbrowser
from os import path

gte_st3 = int(sublime.version()) >= 3000

if gte_st3:
    from .config import *
else:
    from config import *

class HiveOpenCommand(sublime_plugin.WindowCommand):
    def run(self, **args):
        self.init(**args)
        self.show_quick_panel()

    def init(self, **args):
        options = sublime.load_settings(OPTIONS_BASE_NAME)
        self.peek_file = gte_st3 and options.get('peek_file_on_highlight', False)
        self.copy_url_on_open = options.get('copy_url_on_open', False)
        self.binfile_open_in_subl = options.get('open_binary_file_in_sublime', False)

        self.init_item_types(args.get('item_types'))
        self.init_item_data()

        if self.peek_file: self.save_view()

    def init_item_types(self, item_types):
        if not item_types: item_types = DEFAULT_ITEM_TYPES
        self.item_types = list(set(item_types) & set(DEFAULT_ITEM_TYPES))

    def init_item_data(self):
        conf = sublime.load_settings(CONFIG_BASE_NAME)
        self.items = []
        self.view_items = []

        for key in self.item_types:
            if not conf.has(key): continue
            self.items.extend(conf.get(key))

        # sort items alphabetically
        self.items.sort(key=lambda x: x[1].lower())

        for (pathname, desc) in self.items:
            title = desc

            if not title:
                if self.isapp(pathname) or path.isfile(pathname):
                    title = path.basename(pathname) or pathname
                else:
                    title = pathname

            subtitle = '%s %s' % (self.get_item_type(pathname), pathname)
            self.view_items.append([title, subtitle])

    def get_item_type(self, pathname):
        if self.isurl(pathname): return 'URL'
        if self.isapp(pathname): return 'APP'

        if path.isfile(pathname):
            name, ext = path.splitext(pathname)
            return ext[1:].upper() or 'FILE'

        if path.isdir(pathname): return 'DIR'
        return 'UNKNOWN'

    def show_quick_panel(self):
        if gte_st3:
            self.window.show_quick_panel(self.view_items, self.on_done, on_highlight=self.on_highlight)
        else:
            self.window.show_quick_panel(self.view_items, self.on_done)

    def on_done(self, index):
        if self.peek_file: self.restore_view()

        if index == -1: return
        item_name = self.get_name_by_index(index)

        if self.isurl(item_name): return self.open_url(item_name)
        if self.isapp(item_name): return self.open_app(item_name)
        if path.isfile(item_name): return self.open_file(item_name)
        if path.isdir(item_name): return self.open_dir(item_name)

        sublime.status_message('Invalid file/directory name: `%s`.' % item_name)

    def on_highlight(self, index):
        if not self.peek_file: return
        item_name = self.get_name_by_index(index)

        if path.isfile(item_name):
            self.open_file(item_name, True)
        else:
            self.restore_view()

    def open_url(self, url):
        if self.copy_url_on_open:
            sublime.set_clipboard(url)
            sublime.status_message('URL Copied: `%s`' % url)

        if url[0:3] == 'www': url = 'http://' + url
        webbrowser.open_new_tab(url)

    def open_app(self, appname):
        return subprocess.Popen(['open', appname])

    def open_file(self, filename, preview=False):
        if preview: return self.window.open_file(filename, sublime.TRANSIENT)
        name, ext = path.splitext(filename)

        if self.binfile_open_in_subl or not self.is_binary_file(filename):
            self.open_file_inside_subl(filename)
        else:
            self.open_file_outside_subl(filename)

    def open_file_inside_subl(self, filename):
        self.window.open_file(filename)

    def open_file_outside_subl(self, filename):
        if SUBLIME_PLATFORM == 'windows':
            subprocess.Popen(['explorer', filename])

        if SUBLIME_PLATFORM == 'osx':
            subprocess.Popen(['open', filename])

    def open_dir(self, dirname):
        if SUBLIME_PLATFORM == 'windows':
            subprocess.Popen(['explorer', dirname])

        if SUBLIME_PLATFORM == 'osx':
            self.window.run_command('open_dir', { 'dir': dirname })

    def is_binary_file(self, filename):
        textchars = bytearray([7, 8, 9, 10, 12, 13, 27]) + bytearray(range(0x20, 0x100))
        leadbytes = open(filename, 'rb').read(1024)
        return bool(leadbytes.translate(None, textchars))

    def isurl(self, target): return bool(REX_URL.match(target))

    def isapp(self, target):
        if SUBLIME_PLATFORM != 'osx': return False
        return path.splitext(target)[1] == '.app'

    def get_name_by_index(self, index):
        return self.items[index][0]

    def save_view(self):
        self.saved_view = self.window.active_view()
        selection = self.saved_view.sel()
        # save region data as tuple so we can reverse serialization subsequently
        self.saved_regions = [(region.a, region.b) for region in selection]

        # return None if no selection(no viewable cursor)
        # otherwise we only care about the last region(regardless of multi-selection mode)
        return None if not len(selection) else selection[-1]

    def restore_view(self):
        saved_view = self.saved_view
        if saved_view == None: return

        # removes all regions currently if has any
        sublime.Selection.clear(saved_view)

        # restore previous saved regions
        for region in self.saved_regions:
            sublime.Selection.add(saved_view, sublime.Region(*region))

        # focus on previous saved view
        self.window.focus_view(saved_view)

        # scroll the view to center on the last region
        # saved_view.show_at_center(saved_view.sel()[-1])
