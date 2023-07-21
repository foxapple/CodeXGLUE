# -*- coding: utf-8 -*-

import datetime
import sys
import os

# Add flask_velox to the Path
root = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
    )
)

sys.path.append(os.path.join(root, 'doit'))
now = datetime.datetime.utcnow()
year = now.year
version = open(os.path.join(root, 'VERSION')).read().splitlines()[0]

import flask_store  # noqa


# Project details
project = u'Flask-Store'
copyright = u'{0}, Soon London Ltd'.format(year)
version = version
release = version

# Sphinx Config
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinxcontrib.napoleon']

exclude_patterns = []

# Theme
sys.path.append(os.path.abspath('_themes'))
html_theme_path = ['_themes', ]
html_static_path = ['_static', ]
html_theme = 'kr'
html_sidebars = {
    'index':    ['sidebar_intro.html', 'localtoc.html', 'relations.html',
                 'sourcelink.html', 'searchbox.html'],
    '**':       ['sidebar_intro.html', 'localtoc.html', 'relations.html',
                 'sourcelink.html', 'searchbox.html']
}
