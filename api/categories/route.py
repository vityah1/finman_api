# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.categories.services import (
    get_categories_,
    add_category_,
    edit_category_,
    delete_category_,
    get_category_,
)


categories_bp = Blueprint(
    "categories_bp",
    __name__,
)


@categories_bp.route("/api/categories", methods=["GET"])
@cross_origin()
@jwt_required()
def get_categories():
    """
    get categories
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return get_categories_(user_id)


@categories_bp.route("/api/categories", methods=["POST"])
@cross_origin()
@jwt_required()
def add_category():
    """
    add category
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return add_category_(user_id)


@categories_bp.route("/api/categories/<int:category_id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_category(category_id):
    """
    delete category
    """
    return delete_category_(category_id)


@categories_bp.route("/api/categories/<int:category_id>", methods=["PATCH"])
@cross_origin()
@jwt_required()
def edit_category(category_id):
    """
    edit category
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return edit_category_(user_id, category_id)


@categories_bp.route("/api/categories/<int:category_id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_category(category_id):
    """
    get categories
    """
    return get_category_(category_id)
