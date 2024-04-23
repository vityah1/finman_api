import logging
from flask import abort
from sqlalchemy import func
from sqlalchemy import inspect

from .schemas import ConfigTypes
from models.models import SprConfigTypes, Config
from mydb import db


logger = logging.getLogger()


def check_exsists_table(model) -> bool:
    return inspect(db.engine).has_table(model.__tablename__)


def check_and_fill_spr_config_table() -> bool:
    record_count = db.session.query(func.count()).select_from(SprConfigTypes).scalar()
    if record_count == len(list(ConfigTypes)):
        return True

    try:
        for item in list(ConfigTypes):
            data = {
                'type_data': item.value,
                'name': item.name,
                'is_multiple': item.is_multiple,
                'is_need_add_value': item.is_need_add_value,
            }
            user_spr_config_type = db.session().query(SprConfigTypes).filter(
                SprConfigTypes.type_data == item.value,
            ).one_or_none()
            if user_spr_config_type:
                continue
            dictionary_entry = SprConfigTypes()
            dictionary_entry.from_dict(**data)
            db.session.add(dictionary_entry)

        db.session.commit()
        return True
    except Exception as err:
        logger.error(f'Config table check failed\n{err}')
        return False
   

def add_new_config_row(data: dict) -> dict:
    config = Config()
    config.from_dict(**data)
    try:
        db.session().add(config)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'config add failed {err}')
        abort(500, 'config add failed')
    return config.to_dict()
