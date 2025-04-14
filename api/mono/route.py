# _*_ coding:UTF-8 _*_
import logging

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from fastapi import Depends

from api.mono.services import (
    get_mono_user_info_,
    get_mono_users_info_,
    set_webhook_,
    mono_webhook_handler_,
    process_mono_data_payments,
)


router = APIRouter(prefix="/api/mono", tags=["mono"])

mono_logger = logging.getLogger('mono')


@router.get("/users/{user_id}/mono/info/")
def get_user_mono_users_info(user_id: int, _: str = Depends(get_current_user)):
    return get_mono_users_info_(user_id)

@router.get("/users/{mono_user_id}/info/")
def get_mono_user_info(mono_user_id: int, _: str = Depends(get_current_user)):
    return get_mono_user_info_(mono_user_id)

@router.put("/users/{mono_user_id}/webhook")
def set_webhook(mono_user_id: int, _: str = Depends(get_current_user)):
    return set_webhook_(mono_user_id)

@router.get("/users/{mono_user_id}/webhook")
def mono_webhook_test_handler(mono_user_id: int):
    return {'status': 'ok', "mono_user_id": mono_user_id}

@router.post("/users/{mono_user_id}/webhook")
def mono_webhook_handler(mono_user_id: int):
    return mono_webhook_handler_(mono_user_id)

@router.post("/payments")
def get_mono_data_pmts(user_id: str = Depends(get_current_user)):
    return process_mono_data_payments(user_id)
