# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from fastapi import Depends

from api.mono_users.services import (
    get_mono_users_,
    add_mono_user_,
    edit_mono_user_,
    delete_mono_user_,
    get_mono_user_,
)


router = APIRouter(prefix="/api/mono/users", tags=["mono_users"])


@router.get("")
def get_mono_users(user_id: str = Depends(get_current_user)):
    return get_mono_users_(user_id)


@router.post("")
def add_mono_user(user_id: str = Depends(get_current_user)):
    return add_mono_user_(user_id)


@router.delete("/{mono_user_id}")
def delete_mono_user(mono_user_id: str, user_id: str = Depends(get_current_user)):
    return delete_mono_user_(mono_user_id)


@router.patch("/{mono_user_id}")
def edit_mono_user(mono_user_id: str, user_id: str = Depends(get_current_user)):
    return edit_mono_user_(user_id, mono_user_id)


@router.get("/{mono_user_id}")
def get_mono_user(mono_user_id: str, user_id: str = Depends(get_current_user)):
    return get_mono_user_(mono_user_id)
