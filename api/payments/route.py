# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from fastapi import Depends
from pydantic import BaseModel
from typing import Optional, List, Any

from api.payments.services import (
    add_payment_,
    del_payment_,
    upd_payment_,
    get_payment_detail,
    get_payments_detail,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])

class PaymentOut(BaseModel):
    id: int
    rdate: str
    category_id: int
    mydesc: str
    amount: float
    type_payment: Optional[str] = None
    bank_payment_id: Optional[str] = None
    user_id: int
    source: Optional[str] = None
    currency_amount: Optional[float] = None
    currency: Optional[str] = None
    is_deleted: Optional[bool] = None
    category_name: Optional[str] = None
    refuel_data: Optional[Any] = None

class PaymentListResponse(BaseModel):
    data: List[PaymentOut]

class StatusOkResponse(BaseModel):
    status: str

@router.post("", response_model=PaymentOut)
def add_payment(user_id: str = Depends(get_current_user)):
    data = add_payment_(user_id)
    return PaymentOut(**data)

@router.get("", response_model=PaymentListResponse)
def get_payments(user_id: str = Depends(get_current_user)):
    data = get_payments_detail(user_id)
    return PaymentListResponse(data=[PaymentOut(**item) for item in data])

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, user_id: str = Depends(get_current_user)):
    data = get_payment_detail(payment_id)
    return PaymentOut(**data)

@router.delete("/{payment_id}", response_model=StatusOkResponse)
def del_payment(payment_id: int, user_id: str = Depends(get_current_user)):
    res = del_payment_(payment_id)
    # res = {"status": "ok"}
    return StatusOkResponse(**res.json) if hasattr(res, 'json') else StatusOkResponse(**res)

@router.patch("/{payment_id}", response_model=PaymentOut)
def upd_payment(payment_id: int, user_id: str = Depends(get_current_user)):
    data = upd_payment_(payment_id)
    return PaymentOut(**data)
