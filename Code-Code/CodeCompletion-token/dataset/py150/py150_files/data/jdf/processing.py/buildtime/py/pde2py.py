#!/usr/bin/python
"""
    Utility to do whatever mechanical work can be done in converting
    PDE examples to Python ones.
"""
from __future__ import with_statement

from optparse import OptionParser
import os
import re
import shutil
import sys


def usage():
    print >> sys.stderr, 'Usage: pde2py [-f|--force] srcdir destdir'
    sys.exit(1)

parser = OptionParser()
parser.add_option("-f", "--force",
                  action="store_true", dest="force", default=False,
                  help="overwrite existing files")

(opts, args) = parser.parse_args()

if len(args) < 2:
    usage()

src, dest = args
if not (os.path.exists(src) and os.path.isdir(src)):
    usage()
if not os.path.exists(dest):
    os.makedirs(dest)


def copy_dir(s, d):
    if not os.path.exists(d):
        os.mkdir(d)
    for f in os.listdir(s):
        if f[0] == '.':
            continue
        copy(os.path.join(s, f), os.path.join(d, f))


def copy_file(s, d, xform=None):
    with open(s, 'rb') as f:
        text = f.read()
    if xform:
        (d, text) = xform(d, text)
    if os.path.exists(d):
        if opts.force:
            print >> sys.stderr, 'Overwriting %s.' % d
        else:
            print >> sys.stderr, 'Not overwriting %s.' % d
            return
    else:
        print >> sys.stderr, 'Writing %s.' % d

    with open(d, 'wb') as f:
        f.write(text)


def to_python_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def xform_py(d, text):
    text = re.sub('(?<!:)//', '#', text)
    text = text.replace('  ', '    ')
    text = re.sub(r'for *\((?: *int *)?(\w+) *= *0 *; * \1 *< *([^;]+); *\1\+\+ *\)', r'for \1 in range(\2):', text)
    text = re.sub(r'for *\((?: *int *)?(\w+) *= *(\d+) *; * \1 *< *([^;]+); *\1\+\+ *\)', r'for \1 in range(\2, \3):', text)
    text = re.sub(r'for *\((?: *int *)?(\w+) *= *(\d+) *; * \1 *< *([^;]+); *\1 *\+= *([^\)]+)\)', r'for \1 in range(\2, \3, \4):', text)
    text = re.sub(r'(?m)^(\s*)(?:public *)?(?:void|int|float|String)\s+([a-zA-Z0-9]+)\s*\(([^\)]*)\)',
                  r'\1def \2(\3):',
                  text)
    text = re.sub(r'(?:int|float|String|double|Object)\s+([a-zA-Z0-9]+)\s*([,\)])',
                  r'\1\2',
                  text)
    text = re.sub(r'(?:int|float|String|double|Object)\s+([a-zA-Z0-9]+)\s*=',
                  r'\1 =',
                  text)
    text = re.sub(
        r'(?:abstract +)?class +(\w+)', r'class \1(object):', text)
    text = re.sub(
        r'(?m)^\s*(?:abstract\s+)?class\s+(\S+)\s*extends\s*(\S+)\s*$', r'class \1(\2):', text)
    text = re.sub(r'(?m)^(\s*)(?:void|int|float|String)\s+', r'\1', text)
    text = re.sub(r'[{};] *', '', text)
    text = re.sub(r'\n\n+', '\n', text)
    text = re.sub(r'(?m)^(\s*)if\s*\((.+?)\)\s*$', r'\1if \2:', text)
    text = re.sub(r'(?m)^(\s*)else\s+if\s*\((.+?)\)\s*$', r'\1elif \2:', text)
    text = re.sub(r'(?m)^(\s*)else\s*$', r'\1else:', text)
    text = re.sub(r'/\*+| *\*+/', '"""', text)
    text = re.sub(r'(?m)^ *\* *', '', text)
    text = text.replace('new ', '')
    text = text.replace('true', 'True')
    text = text.replace('false', 'False')
    text = text.replace('this.', 'self.')
    text = text.replace('||', 'or')
    text = text.replace('&&', 'and')
    text = re.sub(r'(\w+)\+\+', r'\1 += 1', text)
    text = re.sub(r'(\w+)--', r'\1 -= 1', text)
    text = re.sub(r'(\w+)\.length\b', r'len(\1)', text)

    parent = os.path.dirname(d)
    parent_name = os.path.basename(parent)
    name, ext = os.path.splitext(os.path.basename(d))
    if name == parent_name:
        newext = '.pyde'
    else:
        newext = '.py'
        name = to_python_case(name)

    d = parent + '/' + name + newext
    return (d, text)


def copy(s, d):
    if os.path.isdir(s):
        copy_dir(s, d)
    elif s.endswith(".pde"):
        copy_file(s, d, xform_py)
    else:
        copy_file(s, d)

copy(src, dest)
