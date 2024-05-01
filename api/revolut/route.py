# _*_ coding:UTF-8 _*_
import logging

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.revolut.services import (
    revolut_import_,
)


revolut_bp = Blueprint(
    "revolut_bp",
    __name__,
)

logger = logging.getLogger()


@revolut_bp.route("/api/revolut/import", methods=["POST"])
@cross_origin()
@jwt_required()
def revolut_import():
    """
    import data from revolut
    """
    return revolut_import_()
