from flask import request, abort
from mydb import db
from models import MonoUser

def get_mono_users_(user_id):
    """
    get mono users
    """
    mono_users = db.session().query(MonoUser).filter_by(user_id=user_id).all()
    if not mono_users:
        abort(404, 'Not found mono users')

    return [item.to_dict() for item in mono_users]


def add_mono_user_(user_id: int) -> MonoUser:
    """
    add mono user
    """
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'user add failed {err}')
    data['user_id'] = user_id
    mono_user = MonoUser()
    mono_user.from_dict(**data)
    try:
        db.session().add(mono_user)
        db.session().commit()
    except Exception as err:
        abort(500, f'user add failed {err}')

    return mono_user.to_dict()


def edit_mono_user_(mono_user_id: int) -> MonoUser:
    """
    edit mono user
    """
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'user add failed {err}')

    mono_user = db.session().query(MonoUser).get(mono_user_id)
    if not mono_user:
        abort(404, 'Not found mono users')

    mono_user.from_dict(**data)

    try:
        db.session().commit()
    except Exception as err:
        abort(500, f'user edit failed {err}')

    return mono_user.to_dict()


def delete_mono_user_(mono_user_id: int) -> MonoUser:
    """
    delete mono user
    """

    mono_user = db.session().query(MonoUser).get(mono_user_id)
    if not mono_user:
        abort(404, 'Not found mono users')

    try:
        db.session().delete(mono_user)
        db.session().commit()
    except Exception as err:
        abort(500, f'user delete failed {err}')

    return {"result": "ok"}


def get_mono_user_(mono_user_id: int) -> MonoUser:
    """
    get mono user
    """

    mono_user = db.session().query(MonoUser).get(mono_user_id)
    if not mono_user:
        abort(404, 'Not found mono users')

    return mono_user.to_dict()
