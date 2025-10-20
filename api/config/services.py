import logging

from fastapi import HTTPException
from sqlalchemy import select

from .schemas import ConfigTypes
from models.models import Config, SprConfigTypes
from fastapi_sqlalchemy import db
from .funcs import add_new_config_row
from api.schemas.common import SprConfigTypesResponse, ConfigResponse

logger = logging.getLogger()


def get_config_types_() -> list:
    """
    get config types
    """
    config_types = db.session.query(SprConfigTypes).all()
    if not config_types:
        raise HTTPException(status_code=404, detail='Not found configs')

    return [SprConfigTypesResponse.model_validate(item).model_dump() for item in config_types]


def get_user_config_(user_id: int) -> list[dict]:
    """
    get configs
    """

    stmt = select(
        Config.id,
        Config.type_data,
        Config.value_data,
        Config.add_value
    ).filter(
        Config.user_id == user_id
    )
    configs = db.session.execute(stmt).all()

    if not configs:
        return []

    return [ConfigResponse.model_validate(item).model_dump() for item in configs]


def add_config_(user_id: int, data: dict) -> list[dict]:
    """
    add config
    """
    result = []
    
    is_multiple = True
    # check for add_value
    for type_data in list(ConfigTypes):
        if type_data.value == data['type_data']:
            is_multiple = type_data.is_multiple
            if type_data.is_need_add_value and not data.get('add_value'):
                raise HTTPException(status_code=400, detail='not exist add_value key')

    if not is_multiple:
        stmt = select(Config).where(
            Config.user_id == user_id,
            Config.type_data == data['type_data'],
        )
        user_config = db.session.execute(stmt).scalars().one_or_none()
        if user_config:
            raise HTTPException(status_code=400, detail='not allowed multiple values for this key')

    data['user_id'] = user_id
    result.append(add_new_config_row(data))

    return result


def edit_config_(config_id: int, data: dict) -> dict:
    """
    edit mono user
    """
    config = db.session.query(Config).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail='Not found config')

    config.update(**data)

    try:
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        raise err

    return ConfigResponse.model_validate(config).model_dump()


def delete_config_(config_id: int) -> dict[str, str]:
    """
    delete mono user
    """

    config = db.session.query(Config).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail='Not found config')

    try:
        db.session.delete(config)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        raise err

    return {"result": "ok"}


def get_config_(config_id: int) -> dict:
    """
    get mono user
    """

    config = db.session.query(Config).get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail='Not found config')

    return ConfigResponse.model_validate(config).model_dump()
