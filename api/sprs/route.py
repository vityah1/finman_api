# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.sprs.services import (
    get_spr_dictionary,
)


sprs_bp = Blueprint(
    "sprs_bp",
    __name__,
)


@sprs_bp.route("/api/sprs/<dictionary>", methods=["GET"])
@cross_origin()
# @jwt_required()
def get_dict(dictionary):
    """
    get dictionaries
    """

    # current_user = get_jwt_identity()
    # user_id = current_user.get('user_id')
    return get_spr_dictionary(dictionary)
