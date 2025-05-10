# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, Field

from api.payments.services import (
    add_payment_,
    del_payment_,
    upd_payment_,
    get_payment_detail,
    get_payments_detail,
    change_payments_category_,
    bulk_delete_payments_,
)
from dependencies import get_current_user
from models.models import User

# Створюємо Pydantic моделі для запитів та відповідей
class PaymentBase(BaseModel):
    amount: float = Field(..., description="Сума платежу")
    description: Optional[str] = Field(None, description="Опис платежу")
    category_id: Optional[int] = Field(None, description="ID категорії")
    currency: str = Field("UAH", description="Валюта платежу")
    rdate: Optional[date] = Field(None, description="Дата платежу")

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    amount: Optional[float] = Field(None, description="Сума платежу")
    description: Optional[str] = Field(None, description="Опис платежу")
    category_id: Optional[int] = Field(None, description="ID категорії")
    currency: Optional[str] = Field(None, description="Валюта платежу")
    rdate: Optional[date] = Field(None, description="Дата платежу")

class PaymentCategoryUpdate(BaseModel):
    payment_ids: List[int] = Field(..., description="Список ID платежів")
    category_id: int = Field(..., description="ID нової категорії")

class PaymentBulkDelete(BaseModel):
    payment_ids: List[int] = Field(..., description="Список ID платежів для видалення")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["payments"])


@router.post("/api/payments", status_code=status.HTTP_201_CREATED)
async def add_payment(
    payment: PaymentCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Додавання нового платежу
    """
    return add_payment_(current_user.id, payment_data=payment.dict())


@router.get("/api/payments")
async def get_payments(
    year: Optional[str] = Query(None, description="Рік для фільтрації"),
    month: Optional[str] = Query(None, description="Місяць для фільтрації"),
    q: Optional[str] = Query(None, description="Пошуковий запит"),
    category_id: Optional[int] = Query(None, description="ID категорії для фільтрації"),
    current_user: User = Depends(get_current_user)
):
    """
    Отримання списку платежів з можливістю фільтрації.
    Якщо не вказано рік і місяць, повертаються платежі за поточний місяць.
    Якщо вказано q, виконується пошук.
    """
    # Передаємо всі параметри запиту до сервісу
    params = {
        "year": year,
        "month": month,
        "q": q,
        "category_id": category_id
    }
    return get_payments_detail(current_user.id, params=params)


@router.get("/api/payments/{payment_id}")
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримання інформації про конкретний платіж за ID
    """
    return get_payment_detail(payment_id)


@router.delete("/api/payments/{payment_id}")
async def del_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Видалення платежу за ID
    """
    return del_payment_(payment_id)


@router.patch("/api/payments/{payment_id}")
async def upd_payment(
    payment_id: int,
    payment: PaymentUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Оновлення інформації про платіж
    """
    return upd_payment_(payment_id, payment_data=payment.dict(exclude_unset=True))


@router.post("/api/payments/change-category")
async def change_payments_category(
    update_data: PaymentCategoryUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Змінює категорію для списку платежів
    """
    return change_payments_category_(current_user.id, data=update_data.dict())


@router.post("/api/payments/bulk-delete")
async def bulk_delete_payments(
    delete_data: PaymentBulkDelete = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Масове видалення платежів за списком ID
    """
    return bulk_delete_payments_(current_user.id, data=delete_data.dict())
