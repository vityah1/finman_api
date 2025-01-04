# _*_ coding:UTF-8 _*_
import logging

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.services import bank_import


p24_bp = Blueprint(
    "p24_bp",
    __name__,
)

logger = logging.getLogger()


@p24_bp.route("/api/p24/import", methods=["POST"])
@cross_origin()
@jwt_required()
def p24_import():
    """
    import data from wise
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return bank_import(user_id, 'p24')
