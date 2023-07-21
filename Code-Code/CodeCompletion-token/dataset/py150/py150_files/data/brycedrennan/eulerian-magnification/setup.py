from distutils.core import setup
from eularian_magnification import __version__

setup(
    name='eularian-magnification',
    version=__version__,
    author='Bryce Drennan',
    author_email='eulerian-magnify@brycedrennan.com',
    url='https://github.com/brycedrennan/eulerian-magnification',
    download_url='https://github.com/brycedrennan/eulerian-magnification/tarball/' + __version__,
    keywords=['eulerian magnification', 'opencv', 'motion amplification', 'video'],
    packages=['eularian_magnification'],
    license='MIT',
    description='Amplify tiny movements in video.',
    long_description='Amplify tiny movements in video.',
)