import logging

from flask import request, abort

from mydb import db
from models import Category

logger = logging.getLogger()


def get_categories_(user_id) -> list[dict]:
    """
    get categories
    """
    categories = db.session().query(Category).filter_by(user_id=user_id).all()
    if not categories:
        abort(404, 'Not found categories')

    return [item.to_dict() for item in categories]


def add_category_(user_id: int) -> dict:
    """
    add category
    """
    data = request.get_json()
    data['user_id'] = user_id
    category = Category()
    category.from_dict(**data)
    db.session().add(category)
    db.session().commit()
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
