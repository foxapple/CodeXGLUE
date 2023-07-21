from __future__ import print_function
import os
import sys
import shutil
import getpass
import setuptools

import pipgh


argv = sys.argv[1:]
test_suite = os.environ.get('TOXTESTSUITE', 'tests')


if ('test' in argv and
    (test_suite == 'tests' or ('tests.execution' in test_suite))):

    _q = 'This command will run all test cases. Are you sure? [y/N] '
    try:
        answer = raw_input(_q)
    except NameError:
        answer = input(_q)
    if answer.strip().lower() != 'y':
        exit('')

    try:
        try:
            username = raw_input(u'Username: ')
        except NameError:
            username = input(u'Username: ')
        password = getpass.getpass(u'Password: ')
    except KeyboardInterrupt:
        exit('')

    os.environ['GH_AUTH_USER'] = username
    os.environ['GH_AUTH_PASS'] = password


if 'clean' in argv:
    shutil.rmtree('%s.egg-info' % pipgh.__name__, ignore_errors=True)
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    shutil.rmtree('env', ignore_errors=True)
    def pyclean(path):
        for root, drs, fns in os.walk(path):
            pycache = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache, ignore_errors=True)
            filtered_fns = filter(lambda f: f.endswith('.pyc'), fns)
            for fn in filtered_fns:
                _fn = os.path.join(root, fn)
                os.remove(_fn)
    pyclean(pipgh.__name__)
    pyclean('tests')
    shutil.rmtree('.tox', ignore_errors=True)


long_description = """\
A tool to install python packages from Github.

    Why can't we use Github as a means to share our Python code directly?

*pipgh* searches and installs Python packages from Github. You can further cite a specific branch, release or commit's hash value. This makes the deployment of your Python package as simple as a commit to your repository. (Yup, that means no more wasting of your time!)

Pure Python code (2 and 3 compatible).
"""


setuptools.setup(
    name=pipgh.__name__,
    description=pipgh.__description__,
    long_description=long_description,
    version=pipgh.__version__,
    author='Filipe Funenga',
    author_email='fmafunenga@gmail.com',
    url='https://github.com/ffunenga/%s' % pipgh.__name__,
    license='MIT',
    packages=[pipgh.__name__],
    test_suite = test_suite,
    entry_points = {
        'console_scripts' : [
            '{pkg} = {pkg}:main'.format(pkg=pipgh.__name__)
        ]
    }
)
