#!/usr/bin/env python

from __future__ import print_function

# import 3rd party libraries
from flask.ext.script import Manager
from flask.ext.assets import ManageAssets
from werkzeug.serving import run_simple, WSGIRequestHandler

# patch builtins to add INTERACT
import __builtin__
from utils.pyutils import interact
__builtin__.INTERACT = interact

# import settings and initialize app object
from config import settings
from backend.app import initialize_app
app = initialize_app(settings)

# import libraries
from utils.dbutils import reset_database, DatabaseControlError

# import our code after initialization of app
from config.log import setup_logging
from backend.models import db

setup_logging('scss')

manager = Manager(app)
manager.add_command('assets', ManageAssets())

@manager.command
def runserver(port=5000, bindhost='127.0.0.1'):
    "start the development server"
    class SilentWSGIRequestHandler(WSGIRequestHandler):
        def log_request(self, *args, **kwargs): pass
    run_simple(bindhost, port, app, request_handler=SilentWSGIRequestHandler,
               use_reloader=app.debug, use_debugger=app.debug)

@manager.command
def recreatedb():
    "destroy the database (if any) and recreate it"
    try:
        reset_database(settings.SQLALCHEMY_DATABASE_URI)
    except DatabaseControlError, error:
        print("failed resetting database: %s" % (error,))
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    manager.run()
