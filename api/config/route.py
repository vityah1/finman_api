# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from api.config.services import (
    get_user_config_,
    get_config_,
    add_config_,
    edit_config_,
    delete_config_,
)


config_bp = Blueprint(
    "config_bp",
    __name__,
)


@config_bp.route("/api/users/<int:user_id>/config", methods=["GET"])
@cross_origin()
@jwt_required()
def get_user_config(user_id):
    """
    get configs
    """
    return get_user_config_(user_id)


@config_bp.route("/api/users/<int:user_id>/config", methods=["POST"])
@cross_origin()
@jwt_required()
def add_config(user_id):
    """
    add config
    """
    return add_config_(user_id)


@config_bp.route("/api/config/<config_id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_config(config_id):
    """
    delete config
    """
    return delete_config_(config_id)


@config_bp.route("/api/config/<config_id>", methods=["PATCH"])
@cross_origin()
@jwt_required()
def edit_config(config_id):
    """
    edit config
    """
    return edit_config_(config_id)


@config_bp.route("/api/config/<config_id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_config(config_id):
    """
    get config
    """
    return get_config_(config_id)
