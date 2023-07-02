import logging
from flask import request, abort
from sqlalchemy.orm import aliased

from .schemas import ConfigTypes
from models.models import Config, SprConfigTypes
from mydb import db
from .funcs import add_new_config_row

logger = logging.getLogger()


def get_config_types_() -> list:
    """
    get config types
    """
    config_types = db.session().query(SprConfigTypes).all()
    if not config_types:
        abort(404, 'Not found configs')

    return [item.to_dict() for item in config_types]


def get_user_config_(user_id: int) -> list[dict]:
    """
    get configs
    """

    subquery = db.session().query(Config).filter(Config.user_id == user_id).subquery()
    user_config = aliased(Config, subquery)
    configs = db.session().query(
        SprConfigTypes.name,
        SprConfigTypes.is_need_add_value,
        SprConfigTypes.is_multiple,
        user_config.id,
        SprConfigTypes.type_data,
        user_config.value_data,
        user_config.add_value
    ).outerjoin(
        user_config,
        SprConfigTypes.type_data == user_config.type_data,
    ).all()

    if not configs:
        abort(404, 'Not found configs')

    return [item._asdict() for item in configs]


def add_config_(user_id: int) -> dict:
    """
    add config
    """
    result = []
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'config add failed {err}')
    # chack for add_value
    for type_data in list(ConfigTypes):
        if type_data.value == data['type_data'] \
            and type_data.is_need_add_value \
                and not data.get('add_value'):
            abort(400, 'not exsist add_value key')

    data['user_id'] = user_id
    result.append(add_new_config_row(data))

    return result


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

    config.update(**data)

    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'config edit failed {err}')
        abort(500, 'config edit failed')

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
        db.session().rollback()
        logger.error(f'config delete failed {err}')        
        abort(500, 'config delete failed')

    return {"result": "ok"}


def get_config_(config_id: int) -> Config:
    """
    get mono user
    """

    config = db.session().query(Config).get(config_id)
    if not config:
        abort(404, 'Not found config')

    return config.to_dict()
