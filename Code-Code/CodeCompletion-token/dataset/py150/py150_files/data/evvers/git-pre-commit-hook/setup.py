import codecs
import os
from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(HERE, *parts), 'r').read()


setup(
    name='git-pre-commit-hook',
    description='pre-commit hook for Git',
    long_description=read('README.rst'),
    version='0.0.11',
    license='MIT',
    author='Evgeny Vereshchagin',
    author_email='evvers@ya.ru',
    url='https://github.com/evvers/git-pre-commit-hook',
    packages=find_packages(),
    install_requires=[
        'git-pre-commit-hook-utils >= 0.0.5',
        'flake8',
        'frosted',
        'pep8-naming',
        'restructuredtext_lint >= 0.6.0',
        'PyYAML',
    ],
    entry_points={
        'console_scripts': [
            'git-pre-commit-hook=git_pre_commit_hook:main',
        ],
        'git_pre_commit_hook.extensions': [
            'file_size=git_pre_commit_hook.builtin_plugins.file_size_check',
            'json=git_pre_commit_hook.builtin_plugins.json_check',
            'flake8=git_pre_commit_hook.builtin_plugins.flake8_check',
            'rst=git_pre_commit_hook.builtin_plugins.rst_check',
            'yaml=git_pre_commit_hook.builtin_plugins.yaml_check',
            'frosted=git_pre_commit_hook.builtin_plugins.frosted_check',
            'ini=git_pre_commit_hook.builtin_plugins.ini_check',
            'xml=git_pre_commit_hook.builtin_plugins.xml_check',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Quality Assurance',
    ],
    keywords='git pre-commit hook pep8 pep8-naming flake8 mccabe frosted',
)
