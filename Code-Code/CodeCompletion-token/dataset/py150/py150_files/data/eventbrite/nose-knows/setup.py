import os
import sys

from setuptools import find_packages, setup


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()
VERSION = '0.1.2'

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist bdist_wheel upload')
    print "You should also consider tagging a release:"
    print "  git tag -a %s -m 'version %s'" % (VERSION, VERSION)
    print "  git push --tags"
    sys.exit()


setup(
    name='nose-knows',
    version=VERSION,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    long_description=README + '\n\n' + NEWS,
    url='https://github.com/eventbrite/nose-knows',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'nose.plugins.0.10': ['knows = knows.nose_plugin:KnowsNosePlugin'],
        'pytest11': ['knows = knows.pytest_plugin'],
    },
)
