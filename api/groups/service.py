import datetime
import logging
import uuid

from flask import request, abort
from sqlalchemy import and_

from models import User
from models.models import Group, GroupInvitation, UserGroupAssociation
from mydb import db

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
    # Перевіряємо, чи користувач уже в якійсь групі
    existing_membership = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id
    ).one_or_none()

    if existing_membership:
        abort(400, 'Ви вже є учасником групи. Ви не можете створити нову групу.')

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
        raise err

    # Додаємо власника як учасника групи
    user_group = UserGroupAssociation()
    user_group.user_id = user_id
    user_group.group_id = group.id

    try:
        db.session().add(user_group)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

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
        raise err

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
        raise err

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

    # Оновлений запит для отримання користувачів разом з асоціативними даними
    query_result = db.session().query(
        User, UserGroupAssociation
    ).join(
        UserGroupAssociation, User.id == UserGroupAssociation.user_id
    ).filter(
        UserGroupAssociation.group_id == group_id
    ).all()

    if not query_result:
        abort(404, 'Users not found in this group')

    # Перетворюємо результати в список словників з доданими даними про відносини
    user_list = []
    for user, association in query_result:
        user_dict = user.to_dict()
        user_dict['role'] = association.role
        user_dict['relation_type'] = association.relation_type
        user_list.append(user_dict)

    return user_list


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
        raise err

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
        raise err

    return {"result": "ok"}


def get_group_invitations_(user_id, group_id):
    """
    Отримати запрошення групи
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id:
        abort(403, 'Not authorized to view invitations for this group')

    invitations = db.session().query(GroupInvitation).filter(
        GroupInvitation.group_id == group_id
    ).all()

    return [invitation.to_dict() for invitation in invitations]


def create_group_invitation_(user_id, group_id):
    """
    Створити запрошення до групи
    """
    data = request.get_json()

    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id:
        abort(403, 'Not authorized to create invitations for this group')

    # Перевіряємо, чи вказаний email
    email = data.get('email')

    # Якщо email вказаний, перевіряємо чи вже існує активне запрошення для цього email
    if email:
        existing_invitation = db.session().query(GroupInvitation).filter(
            and_(
                GroupInvitation.group_id == group_id,
                GroupInvitation.email == email,
                GroupInvitation.is_active == True
            )
        ).one_or_none()

        if existing_invitation:
            abort(400, 'Для цього email вже існує активне запрошення')

        # Перевіряємо, чи користувач з таким email вже є в групі
        user_with_email = db.session().query(User).filter(
            User.email == email
        ).one_or_none()

        if user_with_email:
            user_in_group = db.session().query(UserGroupAssociation).filter(
                and_(
                    UserGroupAssociation.user_id == user_with_email.id,
                    UserGroupAssociation.group_id == group_id
                )
            ).one_or_none()

            if user_in_group:
                abort(400, 'Користувач з цим email вже є в групі')

    # Створюємо нове запрошення
    invitation = GroupInvitation()
    invitation.group_id = group_id
    invitation.created_by = user_id
    invitation.invitation_code = str(uuid.uuid4())
    invitation.is_active = True
    invitation.created = datetime.datetime.now(datetime.timezone.utc)

    # Опціональні поля
    if email:
        invitation.email = email

    if 'expires' in data and data['expires']:
        invitation.expires = datetime.datetime.fromisoformat(
            data['expires'].replace('Z', '+00:00')
        )

    try:
        db.session().add(invitation)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    return invitation.to_dict()

def update_user_relation_(user_id_current, group_id, user_id_to_update):
    """
    Оновити інформацію про користувача в групі
    """
    group = db.session().query(Group).get(group_id)
    if not group:
        abort(404, 'Group not found')

    # Перевіряємо, чи користувач є власником групи
    if group.owner_id != user_id_current:
        # Перевіряємо, чи користувач є адміністратором
        user = db.session().query(User).get(user_id_current)
        if not user or not user.is_admin:
            abort(403, 'Not authorized to update users in this group')

    # Перевіряємо, чи користувач є в групі
    user_group = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id_to_update,
        UserGroupAssociation.group_id == group_id
    ).one_or_none()

    if not user_group:
        abort(404, 'User is not in the group')

    # Оновлюємо інформацію про користувача в групі
    try:
        data = request.get_json()
        if 'relation_type' in data:
            user_group.relation_type = data['relation_type']
        if 'role' in data:
            user_group.role = data['role']
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        raise err

    return {"result": "ok"}