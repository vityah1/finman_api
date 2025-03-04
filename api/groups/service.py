import logging

from flask import request, abort

from mydb import db
from models import Group, User, UserGroupAssociation

logger = logging.getLogger()


def get_groups_(user_id) -> list[dict]:
    """
    get groups
    """
    # Перевіряємо, чи користувач є адміністратором
    user = db.session().query(User).get(user_id)
    if not user:
        abort(404, 'User not found')

    if user.is_admin:
        # Якщо користувач є адміністратором, то повертаємо всі групи
        groups = db.session().query(Group).all()
    else:
        # Якщо користувач не є адміністратором, то повертаємо лише групи, в яких він є учасником
        groups = db.session().query(Group).join(
            UserGroupAssociation, Group.id == UserGroupAssociation.group_id
        ).filter(
            UserGroupAssociation.user_id == user_id
        ).all()

    if not groups:
        abort(404, 'Not found groups')

    return [item.to_dict() for item in groups]


def create_group_(user_id: int) -> dict:
    """
    create group
    """
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'group creation failed {err}')

    data['owner_id'] = user_id

    group = Group()
    group.from_dict(**data)

    try:
        db.session().add(group)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'group creation failed {err}')
        abort(500, 'group creation failed')

    # Додаємо власника як учасника групи
    user_group = UserGroupAssociation()
    user_group.user_id = user_id
    user_group.group_id = group.id

    try:
        db.session().add(user_group)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'user group association creation failed {err}')
        abort(500, 'user group association creation failed')

    return group.to_dict()


def update_group_(user_id: int, group_id: int) -> dict:
    """
    update group
    """
    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'group update failed {err}')

    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to update this group')

    group.update(**data)

    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'group update failed {err}')
        abort(500, 'group update failed')

    return group.to_dict()


def delete_group_(user_id: int, group_id: int) -> dict:
    """
    delete group
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to delete this group')

    try:
        # Видаляємо всі асоціації користувачів з групою
        db.session().query(UserGroupAssociation).filter(
            UserGroupAssociation.group_id == group_id
        ).delete()

        # Видаляємо групу
        db.session().delete(group)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'group deletion failed {err}')
        abort(500, 'group deletion failed')

    return {"result": "ok"}


def get_group_(user_id: int, group_id: int) -> dict:
    """
    get group
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи або учасником групи або адміністратором
    is_member = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id,
        UserGroupAssociation.group_id == group_id
    ).one_or_none() is not None

    if not is_member and group.owner_id != user_id:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to view this group')

    return group.to_dict()


def get_group_users_(user_id: int, group_id: int) -> list[dict]:
    """
    get users in group
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи або учасником групи або адміністратором
    is_member = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id,
        UserGroupAssociation.group_id == group_id
    ).one_or_none() is not None

    if not is_member and group.owner_id != user_id:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to view users in this group')

    users = db.session().query(User).join(
        UserGroupAssociation, User.id == UserGroupAssociation.user_id
    ).filter(
        UserGroupAssociation.group_id == group_id
    ).all()

    if not users:
        abort(404, 'Users not found in this group')

    return [user.to_dict() for user in users]


def add_user_to_group_(user_id: int, group_id: int) -> dict:
    """
    add user to group
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to add users to this group')

    try:
        data = request.get_json()
    except Exception as err:
        abort(500, f'user group association creation failed {err}')

    user_id_to_add = data.get('user_id')

    # Перевіряємо, чи користувач існує
    user = db.session().query(User).get(user_id_to_add)
    if not user:
        abort(404, 'User not found')

    # Перевіряємо, чи користувач вже є в групі
    user_group = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id_to_add,
        UserGroupAssociation.group_id == group_id
    ).one_or_none()

    if user_group:
        abort(400, 'User is already in the group')

    # Додаємо користувача до групи
    user_group = UserGroupAssociation()
    user_group.user_id = user_id_to_add
    user_group.group_id = group_id

    try:
        db.session().add(user_group)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'user group association creation failed {err}')
        abort(500, 'user group association creation failed')

    return {"result": "ok"}


def remove_user_from_group_(
        user_id: int, group_id: int, user_id_to_remove: int
) -> dict:
    """
    remove user from group
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to remove users from this group')

    # Перевіряємо, чи користувач не видаляє власника групи
    if group.owner_id == user_id_to_remove:
        abort(400, 'Cannot remove owner from the group')

    # Перевіряємо, чи користувач є в групі
    user_group = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id_to_remove,
        UserGroupAssociation.group_id == group_id
    ).one_or_none()

    if not user_group:
        abort(404, 'User is not in the group')

    # Видаляємо користувача з групи
    try:
        db.session().delete(user_group)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'user group association deletion failed {err}')
        abort(500, 'user group association deletion failed')

    return {"result": "ok"}