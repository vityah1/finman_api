# _*_ coding:UTF-8 _*_

from flask import Blueprint, request, abort, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.invitations.services import (
    check_invitation_, accept_invitation_, get_invitation_,
)

invitations_bp = Blueprint(
    "invitations_bp",
    __name__,
)


@invitations_bp.route("/api/invitations/<string:invitation_code>", methods=["GET"])
@cross_origin()
@jwt_required()
def check_invitation(invitation_code):
    """
    Перевірка запрошення
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return check_invitation_(user_id, invitation_code)


@invitations_bp.route("/api/invitations/<string:invitation_code>/accept", methods=["POST"])
@cross_origin()
@jwt_required()
def accept_invitation(invitation_code):
    """
    Прийняття запрошення
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return accept_invitation_(user_id, invitation_code)


@invitations_bp.route("/api/invitations/<int:invitation_id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_invitation(invitation_id):
    """
    Отримання запрошення
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return get_invitation_(user_id, invitation_id)


@invitations_bp.route("/api/invitations/<int:invitation_id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_invitation(invitation_id):
    """
    Видалення запрошення
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return delete_invitation_(user_id, invitation_id)