import logging

from flask import request, abort

from models.models import Group, UserGroupAssociation
from mydb import db
from models import Category

logger = logging.getLogger()


def get_categories_(user_id) -> list[dict]:
    """
    Отримує категорії для користувача, включаючи категорії групи, якщо користувач є членом групи
    """
    # Спочатку отримуємо категорії, які належать користувачу напряму
    user_categories = db.session().query(Category).filter_by(user_id=user_id).all()

    # Отримуємо групу користувача, якщо вона є
    user_group = db.session().query(Group).join(
        UserGroupAssociation, Group.id == UserGroupAssociation.group_id
    ).filter(
        UserGroupAssociation.user_id == user_id
    ).one_or_none()

    # Якщо користувач є членом групи, додаємо також категорії групи
    group_categories = []
    if user_group:
        group_categories = db.session().query(Category).filter_by(
            group_id=user_group.id
        ).all()

    # Об'єднуємо особисті категорії користувача та категорії групи
    all_categories = user_categories + group_categories

    # Якщо немає жодних категорій, повертаємо стандартний набір
    if not all_categories:
        default_categories = [
            # {"id": 1, "name": "Продукти", "parent_id": 0, "is_visible": True},
            # {"id": 2, "name": "Транспорт", "parent_id": 0, "is_visible": True},
            # {"id": 3, "name": "Розваги", "parent_id": 0, "is_visible": True},
            # {"id": 4, "name": "Комунальні послуги", "parent_id": 0, "is_visible": True},
            # {"id": 5, "name": "Інше", "parent_id": 0, "is_visible": True},
        ]
        return default_categories

    return [item.to_dict() for item in all_categories]


def add_category_(user_id: int) -> dict:
    """
    add category
    """
    data = request.get_json()
    data['user_id'] = user_id

    group = db.session().query(Group).join(
        UserGroupAssociation, Group.id == UserGroupAssociation.group_id
    ).filter(
        UserGroupAssociation.user_id == user_id
    ).one()

    if group:
        data['group_id'] = group.id
    else:
        raise Exception("user not have group")

    category = Category()
    category.from_dict(**data)

    try:
        db.session().add(category)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'Category add failed: {err}')
        abort(500, 'Category add failed')

    return category.to_dict()


def edit_category_(user_id, category_id: int) -> dict:
    """
    edit category
    """
    data = request.get_json()
    category = db.session().query(Category).get(category_id)

    if not category:
        abort(404, 'Not found categories')

    data['user_id'] = user_id
    category.update(**data)

    db.session().commit()
    return category.to_dict()


def delete_category_(category_id: int) -> dict:
    """
    delete category
    """

    category = db.session().query(Category).get(category_id)
    if not category:
        abort(404, 'Not found categories')

    db.session().delete(category)
    db.session().commit()

    return {"result": "ok"}


def get_category_(category_id: int) -> dict:
    """
    get category
    """

    category = db.session().query(Category).get(category_id)
    if not category:
        abort(404, 'Not found categories')

    return category.to_dict()
