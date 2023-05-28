# _*_ coding:UTF-8 _*_
import logging

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from api.mono.services import (
    get_webhook_,
    set_webhook_,
    mono_webhook_handler_,
    get_mono_data_pmts_,
)


mono_bp = Blueprint(
    "mono_bp",
    __name__,
)

mono_logger = logging.getLogger('mono')


@mono_bp.route("/api/mono/webhook/<user>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_webhook(user):
    """
    get current webhook from mono
    """
    return get_webhook_(user)


@mono_bp.route("/api/mono/webhook", methods=["PUT"])
@cross_origin()
@jwt_required()
def set_webhook():
    """
    set a new webhook on mono
    """
    return set_webhook_()


@mono_bp.route("/api/mono/webhook", methods=["POST", "GET"])
@cross_origin()
def mono_webhook_handler():
    """
    insert a new webhook from mono
    input: rdate,cat,sub_cat,mydesc,suma
    """
    return mono_webhook_handler_()


@mono_bp.route("/api/mono/payments", methods=["GET", "POST"])
@cross_origin()
def get_mono_data_pmts():
    return get_mono_data_pmts_()
