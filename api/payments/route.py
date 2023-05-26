# _*_ coding:UTF-8 _*_

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from api.payments.services import (
    add_payment_,
    del_payment_,
    upd_payment_,
    get_payment_,
    get_payments_
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
    insert a new cost
    input: rdate,cat,sub_cat,mydesc,suma
    """
    return add_payment_()


@payments_bp.route("/api/payments/", methods=["GET"])
# @cross_origin(supports_credentials=True)
@cross_origin()
@jwt_required()
def get_payments():
    """
    list or search all costs.
    if not set conditions year and month then get current year and month
    if set q then do search
    input: q,cat,year,month
    """
    return get_payments_()


@payments_bp.route("/api/payments/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_payment(id):
    """
    get info about cost
    input: id
    """
    return get_payment_(id)


@payments_bp.route("/api/payments/<int:id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def del_payment(id):
    """
    mark delete cost
    input: id
    """
    return del_payment_(id)


@payments_bp.route("/api/payments/<id>", methods=["PATCH"])
@cross_origin()
@jwt_required()
def upd_payment(id):
    """
    update a cost
    input: rdate,cat,sub_cat,mydesc,suma,id
    """
    return upd_payment_(id)
