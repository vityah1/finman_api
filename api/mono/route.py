# _*_ coding:UTF-8 _*_
import logging

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from fastapi import Depends
from pydantic import BaseModel, Field, RootModel
from typing import Optional, List, Dict, Any

from api.mono.services import (
    get_mono_user_info_,
    get_mono_users_info_,
    set_webhook_,
    mono_webhook_handler_,
    process_mono_data_payments,
)


router = APIRouter(prefix="/api/mono", tags=["mono"])

mono_logger = logging.getLogger('mono')


class MonoUserOut(BaseModel):
    id: int
    user_id: int
    name: str
    token: str
    created: Optional[str] = None

class MonoUserInfoOut(BaseModel):
    mono_user_id: int
    mono_user_token: str
    this_api_webhook: str
    accounts: Optional[Any] = None
    # інші поля з mono API можуть бути присутні, тому дозволяємо extra
    class Config:
        extra = "allow"

class MonoUserListResponse(BaseModel):
    data: List[MonoUserInfoOut]

class MonoUserResponse(BaseModel):
    data: MonoUserInfoOut

class StatusResponse(BaseModel):
    status: str

class GenericDictResponse(RootModel[Dict[str, Any]]):
    pass

@router.get("/users/{user_id}/mono/info/", response_model=MonoUserListResponse)
def get_user_mono_users_info(user_id: int, _: str = Depends(get_current_user)):
    data = get_mono_users_info_(user_id)
    return MonoUserListResponse(data=[MonoUserInfoOut(**item) for item in data])

@router.get("/users/{mono_user_id}/info/", response_model=MonoUserInfoOut)
def get_mono_user_info(mono_user_id: int, _: str = Depends(get_current_user)):
    data = get_mono_user_info_(mono_user_id)
    return MonoUserInfoOut(**data)

@router.put("/users/{mono_user_id}/webhook", response_model=StatusResponse)
def set_webhook(mono_user_id: int, _: str = Depends(get_current_user)):
    res = set_webhook_(mono_user_id)
    return StatusResponse(**res)

@router.get("/users/{mono_user_id}/webhook", response_model=GenericDictResponse)
def mono_webhook_test_handler(mono_user_id: int):
    return GenericDictResponse(__root__={'status': 'ok', "mono_user_id": mono_user_id})

@router.post("/users/{mono_user_id}/webhook", response_model=StatusResponse)
def mono_webhook_handler(mono_user_id: int):
    res = mono_webhook_handler_(mono_user_id)
    return StatusResponse(**res)

@router.post("/payments", response_model=GenericDictResponse)
def get_mono_data_pmts(user_id: str = Depends(get_current_user)):
    res = process_mono_data_payments(user_id)
    return GenericDictResponse(__root__=res)
