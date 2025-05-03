# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.payments.services import (
    add_payment_,
    del_payment_,
    upd_payment_,
    get_payment_detail,
    get_payments_detail,
    change_payments_category_,
    bulk_delete_payments_,
)

payments_bp = Blueprint(
    "payments_bp",
    __name__,
)


@payments_bp.route("/api/payments", methods=["POST"])
@cross_origin()
@jwt_required()
def add_payment():
    """
    add a new payment from app
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return add_payment_(user_id)


@payments_bp.route("/api/payments", methods=["GET"])
# @cross_origin(supports_credentials=True)
@cross_origin()
@jwt_required()
def get_payments():
    """
    list or search payments by conditions.
    if not set conditions year and month then get current year and month
    if set q then do search
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')

    return get_payments_detail(user_id)


@payments_bp.route("/api/payments/<int:payment_id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_payment(payment_id):
    """
    get info about payment
    input: id
    """
    return get_payment_detail(payment_id)


@payments_bp.route("/api/payments/<int:payment_id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def del_payment(payment_id: int):
    """
    mark delete cost
    input: id
    """
    return del_payment_(payment_id)


@payments_bp.route("/api/payments/<int:payment_id>", methods=["PATCH"])
@cross_origin()
@jwt_required()
def upd_payment(payment_id):
    """
    update payment
    """
    return upd_payment_(payment_id)


@payments_bp.route("/api/payments/change-category", methods=["POST"])
@cross_origin()
@jwt_required()
def change_payments_category():
    """
    Змінює категорію для списку платежів
    Вхідні дані: payment_ids - список ID платежів, category_id - нова категорія
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return change_payments_category_(user_id)


@payments_bp.route("/api/payments/bulk-delete", methods=["POST"])
@cross_origin()
@jwt_required()
def bulk_delete_payments():
    """
    Масове видалення платежів
    Вхідні дані: payment_ids - список ID платежів для видалення
    """
    current_user = get_jwt_identity()
    user_id = current_user.get('user_id')
    return bulk_delete_payments_(user_id)
