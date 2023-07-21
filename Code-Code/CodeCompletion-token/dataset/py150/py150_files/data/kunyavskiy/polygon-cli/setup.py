from setuptools import setup

setup(
        name='polygon-cli',
        version='1.0.8',
        packages=['polygon_cli', 'polygon_cli.actions'],
        url='https://github.com/kunyavskiy/polygon-cli',
        license='MIT',
        author='Pavel Kunyavskiy',
        author_email='kunyavskiy@gmail.com',
        description='Commandline tool for polygon',
        install_requires=['colorama', 'requests', 'prettytable'],
        entry_points={
            'console_scripts': [
                'polygon-cli=polygon_cli:main'
            ],
        }
)
