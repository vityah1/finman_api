import logging

from sqlalchemy import func
from sqlalchemy import inspect
from api.schemas.common import ConfigResponse

from .schemas import ConfigTypes
from models.models import SprConfigTypes, Config
from fastapi_sqlalchemy import db
from mydb import engine, SessionLocal


logger = logging.getLogger()


def check_exsists_table(model) -> bool:
    return inspect(engine).has_table(model.__tablename__)


def check_and_fill_spr_config_table() -> bool:
    """
    Check and fill config table - used during startup (lifespan)
    Uses direct SessionLocal since fastapi_sqlalchemy middleware is not yet initialized
    """
    import traceback
    import sys

    session = SessionLocal()
    try:
        logger.info("Querying SprConfigTypes table...")
        record_count = session.query(func.count()).select_from(SprConfigTypes).scalar()
        logger.info(f"Found {record_count} config types in DB, expected {len(list(ConfigTypes))}")

        if record_count == len(list(ConfigTypes)):
            logger.info("Config table is up to date")
            return True

        logger.info("Adding missing config types...")
        for item in list(ConfigTypes):
            data = {
                'type_data': item.value,
                'name': item.name,
                'is_multiple': item.is_multiple,
                'is_need_add_value': item.is_need_add_value,
            }
            user_spr_config_type = session.query(SprConfigTypes).filter(
                SprConfigTypes.type_data == item.value,
            ).one_or_none()
            if user_spr_config_type:
                continue

            logger.info(f"Adding config type: {item.value}")
            dictionary_entry = SprConfigTypes(**data)
            session.add(dictionary_entry)

        session.commit()
        logger.info("Config table successfully updated")
        return True
    except Exception as err:
        error_msg = f'Config table check failed: {err}'
        logger.error(error_msg)
        logger.error(traceback.format_exc())

        # Print to stderr for visibility
        print(f"\n❌ ERROR in check_and_fill_spr_config_table:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

        session.rollback()
        return False
    finally:
        session.close()
   

def add_new_config_row(data: dict) -> dict:

    config = Config(**data)
    try:
        db.session.add(config)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        raise err

    return ConfigResponse.model_validate(config).model_dump()
