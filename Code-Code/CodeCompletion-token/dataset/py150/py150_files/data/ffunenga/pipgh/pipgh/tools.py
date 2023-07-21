from __future__ import print_function
import sys
import os
import platform
import shutil
import zipfile
import subprocess
try:
    from urllib.request import urlopen
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve
    from urllib2 import urlopen


def test_color_support():
    is_ansi = os.environ.get('TERM', '') == 'ANSI'
    for handle in [sys.stdout, sys.stderr]:
        isatty = hasattr(handle, 'isatty') and handle.isatty()
        if isatty or is_ansi:
            is_windows = platform.system() == 'Windows'
            if is_windows and not is_ansi:
                return False
            else:
                return True
        return False


def force_unicode(s):
    try:
        return unicode(s)
    except NameError:
        return str(s)
normalize = lambda s: u'' if s == None else force_unicode(s)
color_support = test_color_support()
colorize = lambda i, s: (normalize(s) if not color_support
                                      else (i + normalize(s) + u'\033[0m'))
header = lambda s: colorize(u'\033[95m', s)
okblue = lambda s: colorize(u'\033[94m', s)
okgreen = lambda s: colorize(u'\033[92m', s)
warning = lambda s: colorize(u'\033[93m', s)
fail = lambda s: colorize(u'\033[91m', s)
bold = lambda s: colorize(u'\033[1m', s)
underline = lambda s: colorize(u'\033[4m', s)


class URLOpenContext:

    def __init__(self, url):
        self.url = url

    def __enter__(self):
        self.f = urlopen(self.url)
        return self.f

    def __exit__(self, *args):
        self.f.close()


class ShowNode(object):

    def __init__(self, node, level=0):
        self.level = level
        def is_str(s):
            try:
                return type(s) == unicode
            except NameError:
                return type(s) == str
        _test = lambda i: (type(i[1]) == dict or
                           (type(i[1]) != dict and
                            not normalize(i[1]).startswith('http')))
        self.children = [n for n in node.items()]  # if _test(n)]
        self.children.sort(key=lambda i: i[0])

    def __str__(self):
        indent = self.level * u' '
        items = []
        for key, value in self.children:
            if type(value) == dict:
                value = ShowNode(value, self.level + 4)
                indent2 = indent + u'    '
                vals = (indent, okblue(key), indent2, value)
                items.append(u'%s%s:\n%s%s\n' % vals)
            else:
                items.append(u'%s%s: %s\n' % (indent, okblue(key), value))
        rst = u''.join(items).strip()
        return rst


class TempDirContext:

    def __init__(self, path):
        self.path = path
        self.parent_dir = os.getcwd()

    def __enter__(self):
        try:
            os.mkdir(self.path)
        except OSError as e:
            if e.errno != 17:  # File exists
                raise
            shutil.rmtree(self.path)
            os.mkdir(self.path)
        finally:
            os.chdir(self.path)
        return self

    def __exit__(self, *args):
        os.chdir(self.parent_dir)
        try:
            shutil.rmtree(self.path)
        except:
            pass


def unzip(zipfilename, destination):
    with zipfile.ZipFile(zipfilename) as zf:
        zf.extractall(destination)
    for root, ds, fs in os.walk('.'):
        if root == '.':
            root_dir = os.path.join(root, ds[0])
            ini_strip = len(root_dir) + 1
            continue
        target = root[ini_strip:]
        for d in ds:
            source = os.path.join(root, d)
            destination = os.path.join(target, d)
            shutil.move(source, destination)
        for f in fs:
            source = os.path.join(root, f)
            destination = os.path.join(target, f)
            shutil.move(source, destination)
        if root != root_dir:
            break
    shutil.rmtree(root_dir)


def install_one_package(url, output=True):
    with TempDirContext(".pygh") as cwd:
        if output:
            _info = u"Fetching files from '%s'..." % header(url)
            print(_info, file=sys.stderr)
        urlretrieve(url, 'distro.zip')
        unzip('distro.zip', '.')
        args = ['python', 'setup.py', '--fullname']
        full_name = subprocess.check_output(args).decode('utf-8').strip()
        if output:
            _info = u"Installing python package '%s'..." % header(full_name)
            print(_info, file=sys.stderr)
        args = ['python', 'setup.py', 'install']
        with open(os.devnull, 'wb') as shutup:
            return_code = subprocess.check_call(
                    args, stdout=shutup, stderr=shutup)
        if return_code != 0:
            _fmt = u'%s: installation failed with code %d'
            sys.exit(_fmt % (fail('Error'), return_code))
