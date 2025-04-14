# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from fastapi import Depends
from pydantic import BaseModel
from typing import Optional, List

from api.mono_users.services import (
    get_mono_users_,
    add_mono_user_,
    edit_mono_user_,
    delete_mono_user_,
    get_mono_user_,
)


router = APIRouter(prefix="/api/mono/users", tags=["mono_users"])


class MonoUserOut(BaseModel):
    id: int
    user_id: int
    name: str
    token: str
    created: Optional[str] = None

class MonoUserListResponse(BaseModel):
    data: List[MonoUserOut]

class MonoUserResponse(BaseModel):
    data: MonoUserOut

class StatusOkResponse(BaseModel):
    result: str


@router.get("", response_model=MonoUserListResponse)
def get_mono_users(user_id: str = Depends(get_current_user)):
    users = get_mono_users_(user_id)
    return MonoUserListResponse(data=[MonoUserOut(**user) for user in users])


@router.post("", response_model=MonoUserResponse)
def add_mono_user(user_id: str = Depends(get_current_user)):
    user = add_mono_user_(user_id)
    return MonoUserResponse(data=MonoUserOut(**user))


@router.delete("/{mono_user_id}", response_model=StatusOkResponse)
def delete_mono_user(mono_user_id: str, user_id: str = Depends(get_current_user)):
    res = delete_mono_user_(mono_user_id)
    return StatusOkResponse(**res)


@router.patch("/{mono_user_id}", response_model=MonoUserResponse)
def edit_mono_user(mono_user_id: str, user_id: str = Depends(get_current_user)):
    user = edit_mono_user_(user_id, mono_user_id)
    return MonoUserResponse(data=MonoUserOut(**user))


@router.get("/{mono_user_id}", response_model=MonoUserResponse)
def get_mono_user(mono_user_id: str, user_id: str = Depends(get_current_user)):
    user = get_mono_user_(mono_user_id)
    return MonoUserResponse(data=MonoUserOut(**user))
