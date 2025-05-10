import logging

from flask import request, abort

from mydb import db
from models import MonoUser

logger = logging.getLogger()


def get_mono_users_(user_id) -> list[dict]:
    """
    get mono users
    """
    mono_users = db.session().query(MonoUser).filter_by(user_id=user_id).all()
    if not mono_users:
        raise HTTPException(404, 'Not found mono users')

    return [item.to_dict() for item in mono_users]


def add_mono_user_(user_id: int, data: dict) -> dict:
    """
    Додати користувача MonoBank
    
    Параметри:
        user_id: ID користувача
        data: Дані для створення користувача MonoBank
    """
    data['user_id'] = user_id
    mono_user = MonoUser(**data)
    try:
        db.session().add(mono_user)
        db.session().commit()
    except Exception as err:
        logger.error(f'user add failed {err}')
        raise HTTPException(500, 'user add failed')

    return mono_user.to_dict()


def edit_mono_user_(user_id, mono_user_id: int, data: dict) -> dict:
    """
    edit mono user
    """
    mono_user = db.session().query(MonoUser).get(mono_user_id)
    if not mono_user:
        raise HTTPException(404, 'Not found mono users')
    data['user_id'] = user_id
    mono_user.update(**data)

    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    return mono_user.to_dict()


def delete_mono_user_(mono_user_id: int) -> dict:
    """
    delete mono user
    """

    mono_user = db.session().query(MonoUser).get(mono_user_id)
    if not mono_user:
        raise HTTPException(404, 'Not found mono users')

    try:
        db.session().delete(mono_user)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    return {"result": "ok"}


def get_mono_user_(mono_user_id: int) -> dict:
    """
    get mono user
    """

    mono_user = db.session().query(MonoUser).get(mono_user_id)
    if not mono_user:
        raise HTTPException(404, 'Not found mono users')

    return mono_user.to_dict()
