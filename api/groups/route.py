# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from api.groups.service import (
    add_user_to_group_, create_group_, delete_group_, get_group_, get_group_users_,
    get_groups_,
    remove_user_from_group_, update_group_, update_user_relation_,
    get_group_invitations_, create_group_invitation_
)
from dependencies import get_current_user
from models.models import User

# Створюємо Pydantic моделі для запитів та відповідей
class GroupBase(BaseModel):
    name: str = Field(..., description="Назва групи")
    description: Optional[str] = Field(None, description="Опис групи")

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Назва групи")
    description: Optional[str] = Field(None, description="Опис групи")

class GroupUserAdd(BaseModel):
    user_id: int = Field(..., description="ID користувача для додавання")
    role: Optional[str] = Field("member", description="Роль користувача в групі")

class GroupUserUpdate(BaseModel):
    role: str = Field(..., description="Нова роль користувача в групі")

class GroupInvitation(BaseModel):
    email: str = Field(..., description="Email користувача для запрошення")
    role: Optional[str] = Field("member", description="Роль, яка буде призначена користувачу")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["groups"])

@router.patch("/api/groups/{group_id}/users/{user_id}")
async def update_user_relation(
    group_id: int, 
    user_id: int, 
    user_relation: GroupUserUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Оновити інформацію про користувача в групі
    """
    return update_user_relation_(current_user.id, group_id, user_id, role_data=user_relation.dict())


@router.get("/api/groups/{group_id}/invitations")
async def get_group_invitations(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримати запрошення групи
    """
    return get_group_invitations_(current_user.id, group_id)


@router.post("/api/groups/{group_id}/invitations", status_code=status.HTTP_201_CREATED)
async def create_group_invitation(
    group_id: int,
    invitation: GroupInvitation = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Створити запрошення до групи
    """
    return create_group_invitation_(current_user.id, group_id, invitation_data=invitation.dict())


@router.get("/api/groups")
async def get_groups(
    current_user: User = Depends(get_current_user)
):
    """
    Отримати всі групи користувача
    """
    return get_groups_(current_user.id)


@router.post("/api/groups", status_code=status.HTTP_201_CREATED)
async def create_group(
    group: GroupCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Створити нову групу
    """
    return create_group_(current_user.id, group_data=group.dict())


@router.delete("/api/groups/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Видалити групу
    """
    return delete_group_(current_user.id, group_id)


@router.patch("/api/groups/{group_id}")
async def update_group(
    group_id: int,
    group: GroupUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Оновити інформацію про групу
    """
    return update_group_(current_user.id, group_id, group_data=group.dict(exclude_unset=True))


@router.get("/api/groups/{group_id}")
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримати інформацію про групу
    """
    return get_group_(current_user.id, group_id)


@router.get("/api/groups/{group_id}/users")
async def get_group_users(
    group_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Отримати список користувачів в групі
    """
    return get_group_users_(current_user.id, group_id)


@router.post("/api/groups/{group_id}/users")
async def add_user_to_group(
    group_id: int,
    user_data: GroupUserAdd = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Додати користувача до групи
    """
    return add_user_to_group_(current_user.id, group_id, user_data=user_data.dict())


@router.delete("/api/groups/{group_id}/users/{user_id_to_remove}")
async def remove_user_from_group(
    group_id: int,
    user_id_to_remove: int,
    current_user: User = Depends(get_current_user)
):
    """
    Видалити користувача з групи
    """
    return remove_user_from_group_(current_user.id, group_id, user_id_to_remove)
