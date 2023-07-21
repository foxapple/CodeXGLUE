"""Utility functions and classes."""

import os
import shutil
import tempfile
import textwrap

class Tempdir(object):
    """Manage a tempoarary directory

    >>> with Tempdir() as tempdir:
    ...   os.mkdir(os.path.join(tempdir, 'blabla'))
    """

    def __init__(self, cwd=False):
        """Initialize a Tempdir context

        If 'cwd' is True, make the temporary directory the current
        working directory when the context is entered and restore
        the previous working directory when the context is exited.
        """
        self.cwd = cwd

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp()
        if self.cwd:
            self.pwd = os.getcwd()
            os.chdir(self.tempdir)
        return self.tempdir

    def __exit__(self, exception_type, value, traceback):
        if self.cwd:
            os.chdir(self.pwd)
        if os.path.isdir(self.tempdir):
            shutil.rmtree(self.tempdir)
        return False

class Environ(object):
    """Environment variable context

    >>> with Environ(PATH='/bin:/usr/bin'):
    ...   pass
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        self.oldenv = os.environ.copy()
        for k in self.kwargs.keys():
            v = self.kwargs[k]
            if v == None:
                if os.environ.has_key(k):
                    del os.environ[k]
            else:
                os.environ[k] = v
        return os.environ

    def __exit__(self, exception_type, value, traceback):
        os.environ = self.oldenv
        return False

def stripnl(string):
    """Strip the final newline from <string>.

    It is an error if <string> does not end with a newline character,
    except for the empty string, which is okay.

    >>> stripnl('')
    ''
    >>> stripnl('he\\nllo\\n')
    'he\\nllo'
    >>> try:
    ...   stripnl('hello')
    ... except RuntimeError as e:
    ...   e.message
    "string doesn't end in newline: hello"
    """
    if string == '':
        return string
    elif string.endswith('\n'):
        return string[0:-1]
    else:
        raise RuntimeError("string doesn't end in newline: %s" % string)

def dedent(docstring):
    """Dedent a Python docstring treating the first line special.

    This function uses textwrap.dedent() but assumes that the first
    line is not indented.
    """
    lines = docstring.splitlines()
    return '\n'.join((lines[0], textwrap.dedent('\n'.join(lines[1:])),))
