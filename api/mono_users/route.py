# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from api.mono_users.services import (
    get_mono_users_,
    add_mono_user_,
    edit_mono_user_,
    delete_mono_user_,
    get_mono_user_,
)


mono_users_bp = Blueprint(
    "mono_users_bp",
    __name__,
)


@mono_users_bp.route("/api/users/<int:user_id>/mono/users", methods=["GET"])
@cross_origin()
@jwt_required()
def get_mono_users(user_id):
    """
    get mono users
    """
    return get_mono_users_(user_id)


@mono_users_bp.route("/api/users/<int:user_id>/mono/users", methods=["POST"])
@cross_origin()
@jwt_required()
def add_mono_user(user_id):
    """
    get mono users
    """
    return add_mono_user_(user_id)


@mono_users_bp.route("/api/mono/users/<mono_user_id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_mono_user(mono_user_id):
    """
    delete mono users
    """
    return delete_mono_user_(mono_user_id)


@mono_users_bp.route("/api/mono/users/<mono_user_id>", methods=["PATCH"])
@cross_origin()
@jwt_required()
def edit_mono_user(mono_user_id):
    """
    edit mono users
    """
    return edit_mono_user_(mono_user_id)


@mono_users_bp.route("/api/mono/users/<mono_user_id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_mono_user(mono_user_id):
    """
    get mono users
    """
    return get_mono_user_(mono_user_id)
