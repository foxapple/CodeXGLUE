from setuptools import setup, find_packages

version = '0.1.5'

entry_points = [
    "polaris = polaris.cmd:main"
]

install_requires = [
    "Flask-Babel>=0.9",
    "Flask-Login>=0.2.9",
    "Flask-OAuthlib>=0.4.2",
    "Flask-SQLAlchemy>=1.0",
    "Flask-WTF>=0.9.4",
    "Flask>=0.10.1",
    "SQLAlchemy>=0.9.3",
    "alembic>=0.6.3",
    "click>=2.0",
    "dogpile.cache>=0.5.3",
    "gunicorn>=18.0",
    "pandas>=0.13.1",
]

dev_requires = [
    "flake8>=2.1.0",
    "pep8>=1.5.0",
    "yuicompressor>=2.4.8",
]

test_requires = [
    "flake8>=2.1.0",
    "lxml>=3.3.3",
    "nose>=1.3.1",
]

postgres_requires = [
    "psycopg2>=2.5.2",
]

mysql_requires = [
    "pymysql>=0.6.1",
]

setup(name='polaris',
      version=version,
      description="Dashboard made easy.",
      long_description="",
      keywords='data virtualization analysis dashboard',
      author='Lx Yu',
      author_email='i@lxyu.net',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      entry_points={"console_scripts": entry_points},
      install_requires=install_requires,
      extras_require={
          "dev": dev_requires,
          "tests": test_requires,
          "postgres": postgres_requires,
          "mysql": mysql_requires
      },
      classifiers=[
          "Topic :: Software Development"
          "Topic :: Scientific/Engineering :: Visualization",
          "Development Status :: 4 - Beta",
          "Framework :: Flask",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
      ])
