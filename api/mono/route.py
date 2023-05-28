# _*_ coding:UTF-8 _*_
import logging

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from api.mono.services import (
    get_mono_user_info_,
    set_webhook_,
    mono_webhook_handler_,
    get_mono_data_pmts_,
)


mono_bp = Blueprint(
    "mono_bp",
    __name__,
)

mono_logger = logging.getLogger('mono')


@mono_bp.route("/api/users/<int:user_id>/mono/info/", methods=["GET"])
@cross_origin()
@jwt_required()
def get_mono_user_info(user_id: int):
    """
    get current webhook from mono
    """
    return get_mono_user_info_(user_id)


@mono_bp.route("/api/mono/users/<int:mono_user_id>/webhook", methods=["PUT"])
@cross_origin()
@jwt_required()
def set_webhook(mono_user_id: int):
    """
    set a new webhook on mono
    """
    return set_webhook_(mono_user_id)


@mono_bp.route("/api/mono/users/<int:mono_user_id>/webhook", methods=["POST", "GET"])
@cross_origin()
def mono_webhook_handler(mono_user_id: int):
    """
    insert a new webhook from mono
    input: rdate,cat,sub_cat,mydesc,suma
    """
    return mono_webhook_handler_(mono_user_id)


@mono_bp.route("/api/mono/payments", methods=["GET", "POST"])
@cross_origin()
@jwt_required()
def get_mono_data_pmts():
    return get_mono_data_pmts_()
