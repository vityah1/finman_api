# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from api.invitations.services import (
    check_invitation_, accept_invitation_, check_user_invitations_, delete_invitation_,
    get_invitation_, ignore_invitation_,
)
from dependencies import get_current_user
from models.models import User

# Pydantic моделі для запитів та відповідей
class InvitationAccept(BaseModel):
    accept_data: Optional[Dict[str, Any]] = Field(None, description="Додаткові дані для прийняття запрошення")

class InvitationIgnore(BaseModel):
    ignore_reason: Optional[str] = Field(None, description="Причина ігнорування запрошення")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["invitations"])

@router.get("/api/invitations/{invitation_code}")
async def check_invitation(
    invitation_code: str, 
    current_user: User = Depends(get_current_user)
):
    """
    Перевірка запрошення
    """
    return check_invitation_(current_user.id, invitation_code)


@router.post("/api/invitations/{invitation_code}/accept")
async def accept_invitation(
    invitation_code: str,
    accept_data: Optional[InvitationAccept] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """
    Прийняття запрошення
    """
    data = None
    if accept_data:
        data = accept_data.model_dump()
    return accept_invitation_(current_user.id, invitation_code, data)


@router.get("/api/invitations/{invitation_id}")
async def get_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримання запрошення
    """
    return get_invitation_(current_user.id, invitation_id)


@router.delete("/api/invitations/{invitation_id}")
async def delete_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Видалення запрошення
    """
    return delete_invitation_(current_user.id, invitation_id)


@router.get("/api/invitations")
async def check_user_invitations(
    current_user: User = Depends(get_current_user)
):
    """
    Перевірка наявності запрошень для поточного користувача
    """
    return check_user_invitations_(current_user.id)


@router.post("/api/invitations/{invitation_id}/ignore")
async def ignore_invitation(
    invitation_id: int,
    ignore_data: Optional[InvitationIgnore] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """
    Ігнорування запрошення
    """
    data = None
    if ignore_data:
        data = ignore_data.dict()
    return ignore_invitation_(current_user.id, invitation_id, data)