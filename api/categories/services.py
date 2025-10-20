import logging
from fastapi import HTTPException
from api.schemas.common import CategoryResponse


from models.models import Group, UserGroupAssociation
from fastapi_sqlalchemy import db
from models import Category

logger = logging.getLogger()


def get_categories_(user_id) -> list[dict]:
    """
    Отримує категорії для користувача, включаючи категорії групи, якщо користувач є членом групи
    """
    # Спочатку отримуємо категорії, які належать користувачу напряму
    user_categories = db.session.query(Category).filter_by(user_id=user_id).all()

    # Отримуємо групу користувача, якщо вона є
    user_group = db.session.query(Group).join(
        UserGroupAssociation, Group.id == UserGroupAssociation.group_id
    ).filter(
        UserGroupAssociation.user_id == user_id
    ).one_or_none()

    # Якщо користувач є членом групи, додаємо також категорії групи
    group_categories = []
    if user_group:
        group_categories = db.session.query(Category).filter_by(
            group_id=user_group.id
        ).all()

    # Об'єднуємо особисті категорії користувача та категорії групи, уникаючи дублікатів
    # Використовуємо словник, де ключем є id категорії для забезпечення унікальності
    unique_categories = {}
    
    # Додаємо спочатку особисті категорії
    for category in user_categories:
        unique_categories[category.id] = category
    
    # Додаємо категорії групи, уникаючи дублікатів
    for category in group_categories:
        if category.id not in unique_categories:
            unique_categories[category.id] = category
    
    # Отримуємо список унікальних категорій
    all_categories = list(unique_categories.values())

    return [CategoryResponse.model_validate(item).model_dump() for item in all_categories]


def add_category_(user_id: int, data: dict) -> dict:
    """
    add category
    """
    data['user_id'] = user_id

    group = db.session.query(Group).join(
        UserGroupAssociation, Group.id == UserGroupAssociation.group_id
    ).filter(
        UserGroupAssociation.user_id == user_id
    ).one()

    if group:
        data['group_id'] = group.id
    else:
        raise Exception("user not have group")

    category = Category(**data)

    try:
        db.session.add(category)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        raise err

    return CategoryResponse.model_validate(category).model_dump()


def edit_category_(user_id, category_id: int, data: dict) -> dict:
    """
    edit category
    """
    category = db.session.query(Category).get(category_id)

    if not category:
        raise HTTPException(404, 'Not found categories')

    data['user_id'] = user_id
    category.update(**data)

    db.session.commit()
    return CategoryResponse.model_validate(category).model_dump()


def delete_category_(category_id: int) -> dict:
    """
    delete category
    """

    category = db.session.query(Category).get(category_id)
    if not category:
        raise HTTPException(404, 'Not found categories')

    db.session.delete(category)
    db.session.commit()

    return {"result": "ok"}


def get_category_(category_id: int) -> dict:
    """
    get category
    """

    category = db.session.query(Category).get(category_id)
    if not category:
        raise HTTPException(404, 'Not found categories')

    return CategoryResponse.model_validate(category).model_dump()
