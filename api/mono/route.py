# _*_ coding:UTF-8 _*_
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from pydantic import BaseModel, Field

from api.mono.services import (
    get_mono_user_info_,
    get_mono_users_info_,
    set_webhook_,
    mono_webhook_handler_,
    process_mono_data_payments,
)
from dependencies import get_current_user
from models.models import User

# Pydantic моделі для запитів та відповідей
class MonoWebhookRequest(BaseModel):
    webhook_url: str = Field(..., description="URL для встановлення вебхуку")

class MonoPaymentProcessRequest(BaseModel):
    mono_user_id: int = Field(..., description="ID користувача Mono")
    from_date: Optional[str] = Field(None, description="Початкова дата (формат: YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="Кінцева дата (формат: YYYY-MM-DD)")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["mono"])

mono_logger = logging.getLogger('mono')


@router.get("/api/users/{user_id}/mono/info/")
async def get_user_mono_users_info(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримати інформацію про користувачів Monobank
    """
    return get_mono_users_info_(user_id)


@router.get("/api/mono/users/{mono_user_id}/info/")
async def get_mono_user_info(
    mono_user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримати інформацію про конкретного користувача Monobank
    """
    return get_mono_user_info_(mono_user_id)


@router.put("/api/mono/users/{mono_user_id}/webhook")
async def set_webhook(
    mono_user_id: int,
    webhook_data: MonoWebhookRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Встановити новий вебхук для Monobank
    """
    return set_webhook_(mono_user_id, webhook_data.webhook_url)


@router.get("/api/mono/users/{mono_user_id}/webhook")
async def mono_webhook_test_handler(mono_user_id: int):
    """
    Тестовий обробник для вебхуків Monobank
    """
    return {'status': 'ok', "mono_user_id": mono_user_id}


@router.post("/api/mono/users/{mono_user_id}/webhook")
async def mono_webhook_handler(mono_user_id: int, webhook_data: Dict[str, Any] = Body(...)):
    """
    Обробник вебхуків від Monobank
    """
    return mono_webhook_handler_(mono_user_id, webhook_data)


@router.post("/api/mono/payments")
async def get_mono_data_pmts(
    payment_data: MonoPaymentProcessRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Обробка платежів від Monobank
    """
    return process_mono_data_payments(current_user.id, payment_data.dict())
