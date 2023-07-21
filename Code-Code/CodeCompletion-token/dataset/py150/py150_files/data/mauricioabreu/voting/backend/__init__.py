from sqlalchemy import engine_from_config

from backend.helpers import parse_config


def create_engine(settings):
    config = parse_config(settings)
    settings = dict(config.items('sqlalchemy'))
    engine = engine_from_config(settings)

    return engine
