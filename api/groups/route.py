# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.groups.service import (
    add_user_to_group_, create_group_, delete_group_, get_group_, get_group_users_,
    get_groups_,
    remove_user_from_group_, update_group_,
)

groups_bp = Blueprint(
    "groups_bp",
    __name__,
)


@groups_bp.route("/api/groups", methods=["GET"])
@cross_origin()
@jwt_required()
def get_groups():
    """
    get groups
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return get_groups_(user_id)


@groups_bp.route("/api/groups", methods=["POST"])
@cross_origin()
@jwt_required()
def create_group():
    """
    create a group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return create_group_(user_id)


@groups_bp.route("/api/groups/<int:group_id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_group(group_id):
    """
    delete group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return delete_group_(user_id, group_id)


@groups_bp.route("/api/groups/<int:group_id>", methods=["PATCH"])
@cross_origin()
@jwt_required()
def update_group(group_id):
    """
    update group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return update_group_(user_id, group_id)


@groups_bp.route("/api/groups/<int:group_id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_group(group_id):
    """
    get group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return get_group_(user_id, group_id)


@groups_bp.route("/api/groups/<int:group_id>/users", methods=["GET"])
@cross_origin()
@jwt_required()
def get_group_users(group_id):
    """
    get users in group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return get_group_users_(user_id, group_id)


@groups_bp.route("/api/groups/<int:group_id>/users", methods=["POST"])
@cross_origin()
@jwt_required()
def add_user_to_group(group_id):
    """
    add user to group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return add_user_to_group_(user_id, group_id)


@groups_bp.route("/api/groups/<int:group_id>/users/<int:user_id_to_remove>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def remove_user_from_group(group_id, user_id_to_remove):
    """
    remove user from group
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return remove_user_from_group_(user_id, group_id, user_id_to_remove)