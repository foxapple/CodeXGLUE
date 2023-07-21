"""App
"""


from flask import Flask

from .views import api
from .models import db

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.register_blueprint(api, url_prefix='/api/v1')

    db.init_app(app)

    return app
