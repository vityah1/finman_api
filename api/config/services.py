from flask import request, abort
from models.models import Config
from mydb import db


def get_configs_(user_id):
    """
    get configs
    """
    configs = db.session().query(Config).filter_by(user_id=user_id).all()
    if not configs:
        abort(404, 'Not found configs')

    return [item.to_dict() for item in configs]


def add_config_(user_id: int) -> Config:
    """
    add config
    """
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'config add failed {err}')
    data['user_id'] = user_id
    config = Config()
    config.from_dict(**data)
    try:
        db.session().add(config)
        db.session().commit()
    except Exception as err:
        abort(500, f'config add failed {err}')

    return config.to_dict()


def edit_config_(config_id: int) -> Config:
    """
    edit mono user
    """
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'config add failed {err}')

    config = db.session().query(Config).get(config_id)
    if not config:
        abort(404, 'Not found config')

    config.from_dict(**data)

    try:
        db.session().commit()
    except Exception as err:
        abort(500, f'config edit failed {err}')

    return config.to_dict()


def delete_config_(config_id: int) -> Config:
    """
    delete mono user
    """

    config = db.session().query(Config).get(config_id)
    if not config:
        abort(404, 'Not found config')

    try:
        db.session().delete(config)
        db.session().commit()
    except Exception as err:
        abort(500, f'config delete failed {err}')

    return {"result": "ok"}


def get_config_(config_id: int) -> Config:
    """
    get mono user
    """

    config = db.session().query(Config).get(config_id)
    if not config:
        abort(404, 'Not found config')

    return config.to_dict()
