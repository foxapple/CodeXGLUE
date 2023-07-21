from setuptools import setup, find_packages

INFO = {'name': 'BTSync',
        'version': '0.0.1',
        }

setup(
    name=INFO['name'],
    version=INFO['version'],
    author='Jack Minardi',
    packages=find_packages(),
    zip_safe=False,
    maintainer='Jack Minardi',
    maintainer_email='jack@minardi.org',
    py_modules=['btsync'],
)
