import os
from setuptools import setup

setup(
    name = "mash",
    version = "0.0.1",
    author = "Adam 'Cezar' Jenkins",
    author_email = "emperorcezar@gmail.com",
    description = ("Django deployment and configuration tool that takes it's inspiration from heroku."),
    license = "BSD",
    keywords = "django deployment",
    url = "http://packages.python.org/mash",
    packages=['mash',],
    scripts=['bin/mash'],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires = ['fabric', 'pyyaml', 'gitpython'],
)
