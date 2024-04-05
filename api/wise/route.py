# _*_ coding:UTF-8 _*_
import logging

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.wise.services import (
    wise_import_,
)


wise_bp = Blueprint(
    "wise_bp",
    __name__,
)

logger = logging.getLogger()


@wise_bp.route("/api/wise/import", methods=["POST"])
@cross_origin()
@jwt_required()
def wise_import():
    """
    import data from wise
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return wise_import_(user_id)
