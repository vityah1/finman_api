import logging
import datetime
from sqlalchemy import and_

from flask import abort, jsonify
from models.models import Group, GroupInvitation, User, UserGroupAssociation
from mydb import db

logger = logging.getLogger()


def check_invitation_(user_id, invitation_code):
    """
    Перевірка запрошення
    """
    invitation = db.session().query(GroupInvitation).filter(
        and_(
            GroupInvitation.invitation_code == invitation_code,
            GroupInvitation.is_active == True
        )
    ).one_or_none()

    if not invitation:
        abort(404, 'Запрошення не знайдено або воно неактивне')

    # Перевіряємо, чи дійсне запрошення за часом
    if invitation.expires and invitation.expires < datetime.datetime.now(
            datetime.timezone.utc
    ):
        abort(400, 'Термін дії запрошення закінчився')

    # Перевіряємо, чи користувач вже в групі
    user_in_group = db.session().query(UserGroupAssociation).filter(
        and_(
            UserGroupAssociation.user_id == user_id,
            UserGroupAssociation.group_id == invitation.group_id
        )
    ).one_or_none()

    if user_in_group:
        abort(400, 'Ви вже є учасником цієї групи')

    # Отримуємо дані про групу та користувача, який створив запрошення
    group = db.session().query(Group).get(invitation.group_id)
    creator = db.session().query(User).get(invitation.created_by)

    result = invitation.to_dict()
    result['group'] = group.to_dict()
    result['creator'] = creator.to_dict()

    return result


def accept_invitation_(user_id, invitation_code):
    """
    Прийняття запрошення
    """

    # Перевіряємо, чи користувач уже в якійсь групі
    existing_membership = db.session().query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == user_id
    ).one_or_none()

    if existing_membership:
        abort(
            400,
            'Ви вже є учасником іншої групи. Вийдіть з неї перед приєднанням до нової.'
        )

    invitation = db.session().query(GroupInvitation).filter(
        and_(
            GroupInvitation.invitation_code == invitation_code,
            GroupInvitation.is_active == True
        )
    ).one_or_none()

    if not invitation:
        abort(404, 'Запрошення не знайдено або воно неактивне')

    # Перевіряємо, чи дійсне запрошення за часом
    if invitation.expires and invitation.expires < datetime.datetime.now(
            datetime.timezone.utc
    ):
        abort(400, 'Термін дії запрошення закінчився')

    # Перевіряємо, чи користувач вже в групі
    user_in_group = db.session().query(UserGroupAssociation).filter(
        and_(
            UserGroupAssociation.user_id == user_id,
            UserGroupAssociation.group_id == invitation.group_id
        )
    ).one_or_none()

    if user_in_group:
        abort(400, 'Ви вже є учасником цієї групи')

    # Додаємо користувача до групи
    user_group = UserGroupAssociation()
    user_group.user_id = user_id
    user_group.group_id = invitation.group_id
    user_group.role = 'member'
    user_group.joined_at = datetime.datetime.now(datetime.timezone.utc)

    try:
        db.session().add(user_group)

        # Якщо запрошення було на електронну пошту, деактивуємо його
        if invitation.email:
            invitation.is_active = False

        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'Помилка при прийнятті запрошення: {err}')
        abort(500, 'Помилка при прийнятті запрошення')

    return jsonify({"result": "ok", "message": "Ви успішно приєднались до групи"})


def get_invitation_(user_id, invitation_id):
    """
    Отримання запрошення
    """
    invitation = db.session().query(GroupInvitation).get(invitation_id)

    if not invitation:
        abort(404, 'Запрошення не знайдено')

    # Перевіряємо, чи користувач має право переглядати це запрошення
    group = db.session().query(Group).get(invitation.group_id)

    if group.owner_id != user_id:
        abort(403, 'У вас немає доступу до цього запрошення')

    return invitation.to_dict()


def delete_invitation_(user_id, invitation_id):
    """
    Видалення запрошення
    """
    invitation = db.session().query(GroupInvitation).get(invitation_id)

    if not invitation:
        abort(404, 'Запрошення не знайдено')

    # Перевіряємо, чи користувач має право видаляти це запрошення
    group = db.session().query(Group).get(invitation.group_id)

    if group.owner_id != user_id:
        abort(403, 'У вас немає доступу для видалення цього запрошення')

    try:
        # Деактивуємо запрошення замість видалення
        invitation.is_active = False
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'Помилка при видаленні запрошення: {err}')
        abort(500, 'Помилка при видаленні запрошення')

    return jsonify({"result": "ok"})