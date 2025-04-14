# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from pydantic import BaseModel
from typing import Optional, List

from api.groups.service import (
    add_user_to_group_, create_group_, delete_group_, get_group_, get_group_users_,
    get_groups_,
    remove_user_from_group_, update_group_, update_user_relation_,
)

# Додаємо новий імпорт
from api.groups.service import (
    get_group_invitations_, create_group_invitation_
)

router = APIRouter(prefix="/api/groups", tags=["groups"])

class GroupOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int

class GroupListResponse(BaseModel):
    data: List[GroupOut]

class GroupResponse(BaseModel):
    data: GroupOut

class StatusOkResponse(BaseModel):
    result: str

class UserWithGroupRoleOut(BaseModel):
    id: int
    login: str
    fullname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    relation_type: Optional[str] = None

class UserListResponse(BaseModel):
    data: List[UserWithGroupRoleOut]

class GroupInvitationOut(BaseModel):
    id: int
    group_id: int
    created_by: int
    invitation_code: str
    email: Optional[str] = None
    is_active: Optional[bool] = None
    created: Optional[str] = None
    expires: Optional[str] = None

class GroupInvitationListResponse(BaseModel):
    data: List[GroupInvitationOut]

@router.patch("/{group_id}/users/{user_id}", response_model=StatusOkResponse)
def update_user_relation(group_id: int, user_id: int, user_id_current: str = Depends(get_current_user)):
    res = update_user_relation_(user_id_current, group_id, user_id)
    return StatusOkResponse(**res)

@router.get("/{group_id}/invitations", response_model=GroupInvitationListResponse)
def get_group_invitations(group_id: int, user_id: str = Depends(get_current_user)):
    data = get_group_invitations_(user_id, group_id)
    return GroupInvitationListResponse(data=[GroupInvitationOut(**inv) for inv in data])

@router.post("/{group_id}/invitations", response_model=GroupInvitationOut)
def create_group_invitation(group_id: int, user_id: str = Depends(get_current_user)):
    inv = create_group_invitation_(user_id, group_id)
    return GroupInvitationOut(**inv)

@router.get("", response_model=GroupListResponse)
def get_groups(user_id: str = Depends(get_current_user)):
    groups = get_groups_(user_id)
    return GroupListResponse(data=[GroupOut(**g) for g in groups])

@router.post("", response_model=GroupResponse)
def create_group(user_id: str = Depends(get_current_user)):
    group = create_group_(user_id)
    return GroupResponse(data=GroupOut(**group))

@router.delete("/{group_id}", response_model=StatusOkResponse)
def delete_group(group_id: int, user_id: str = Depends(get_current_user)):
    res = delete_group_(user_id, group_id)
    return StatusOkResponse(**res)

@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(group_id: int, user_id: str = Depends(get_current_user)):
    group = update_group_(user_id, group_id)
    return GroupResponse(data=GroupOut(**group))

@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, user_id: str = Depends(get_current_user)):
    group = get_group_(user_id, group_id)
    return GroupResponse(data=GroupOut(**group))

@router.get("/{group_id}/users", response_model=UserListResponse)
def get_group_users(group_id: int, user_id: str = Depends(get_current_user)):
    users = get_group_users_(user_id, group_id)
    return UserListResponse(data=[UserWithGroupRoleOut(**u) for u in users])

@router.post("/{group_id}/users", response_model=StatusOkResponse)
def add_user_to_group(group_id: int, user_id: str = Depends(get_current_user)):
    res = add_user_to_group_(user_id, group_id)
    return StatusOkResponse(**res)

@router.delete("/{group_id}/users/{user_id_to_remove}", response_model=StatusOkResponse)
def remove_user_from_group(group_id: int, user_id_to_remove: int, user_id: int = Depends(get_current_user)):
    res = remove_user_from_group_(user_id, group_id, user_id_to_remove)
    return StatusOkResponse(**res)