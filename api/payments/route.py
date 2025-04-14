# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from fastapi import Depends

from api.payments.services import (
    add_payment_,
    del_payment_,
    upd_payment_,
    get_payment_detail,
    get_payments_detail,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("")
def add_payment(user_id: str = Depends(get_current_user)):
    return add_payment_(user_id)


@router.get("")
def get_payments(user_id: str = Depends(get_current_user)):
    return get_payments_detail(user_id)


@router.get("/{payment_id}")
def get_payment(payment_id: int, user_id: str = Depends(get_current_user)):
    return get_payment_detail(payment_id)


@router.delete("/{payment_id}")
def del_payment(payment_id: int, user_id: str = Depends(get_current_user)):
    return del_payment_(payment_id)


@router.patch("/{payment_id}")
def upd_payment(payment_id: int, user_id: str = Depends(get_current_user)):
    return upd_payment_(payment_id)
