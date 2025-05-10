# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from api.mono_users.services import (
    get_mono_users_,
    add_mono_user_,
    edit_mono_user_,
    delete_mono_user_,
    get_mono_user_,
)
from dependencies import get_current_user
from models.models import User

# Pydantic моделі для запитів та відповідей
class MonoUserCreate(BaseModel):
    token: str = Field(..., description="Токен mono API")
    name: Optional[str] = Field(None, description="Назва для користувача")

class MonoUserUpdate(BaseModel):
    token: Optional[str] = Field(None, description="Токен mono API")
    name: Optional[str] = Field(None, description="Назва для користувача")
    status: Optional[bool] = Field(None, description="Статус активності")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["mono_users"])


@router.get("/api/mono/users")
async def get_mono_users(
    current_user: User = Depends(get_current_user)
):
    """
    Отримання списку всіх користувачів Mono
    """
    return get_mono_users_(current_user.id)


@router.post("/api/mono/users", status_code=status.HTTP_201_CREATED)
async def add_mono_user(
    mono_user: MonoUserCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Додавання нового користувача Mono
    """
    return add_mono_user_(current_user.id, mono_user.dict())


@router.delete("/api/mono/users/{mono_user_id}")
async def delete_mono_user(
    mono_user_id: int = Path(...),
    current_user: User = Depends(get_current_user)
):
    """
    Видалення користувача Mono
    """
    return delete_mono_user_(mono_user_id)


@router.patch("/api/mono/users/{mono_user_id}")
async def edit_mono_user(
    mono_user_id: int = Path(...),
    mono_user_data: MonoUserUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Редагування користувача Mono
    """
    return edit_mono_user_(current_user.id, mono_user_id, mono_user_data.dict(exclude_unset=True))


@router.get("/api/mono/users/{mono_user_id}")
async def get_mono_user(
    mono_user_id: int = Path(...),
    current_user: User = Depends(get_current_user)
):
    """
    Отримання даних конкретного користувача Mono
    """
    return get_mono_user_(mono_user_id)
