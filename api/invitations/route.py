# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from api.invitations.services import (
    check_invitation_, accept_invitation_, check_user_invitations_, delete_invitation_,
    get_invitation_, ignore_invitation_,
)
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/invitations", tags=["invitations"])

class GroupShortOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int

class UserShortOut(BaseModel):
    id: int
    login: str
    fullname: Optional[str] = None
    email: Optional[str] = None

class InvitationOut(BaseModel):
    id: int
    group_id: int
    created_by: int
    invitation_code: str
    email: Optional[str] = None
    is_active: Optional[bool] = None
    created: Optional[str] = None
    expires: Optional[str] = None
    group: Optional[GroupShortOut] = None
    creator: Optional[UserShortOut] = None

class InvitationListResponse(BaseModel):
    data: List[InvitationOut]

class StatusOkResponse(BaseModel):
    result: str
    message: Optional[str] = None

@router.get("/{invitation_code}", response_model=InvitationOut)
def check_invitation(invitation_code: str, user_id: str = Depends(get_current_user)):
    data = check_invitation_(user_id, invitation_code)
    return InvitationOut(**data)

@router.post("/{invitation_code}/accept", response_model=StatusOkResponse)
def accept_invitation(invitation_code: str, user_id: str = Depends(get_current_user)):
    res = accept_invitation_(user_id, invitation_code)
    # res = {"result": "ok", "message": ...}
    return StatusOkResponse(**res.json) if hasattr(res, 'json') else StatusOkResponse(**res)

@router.get("/{invitation_id}", response_model=InvitationOut)
def get_invitation(invitation_id: int, user_id: str = Depends(get_current_user)):
    data = get_invitation_(user_id, invitation_id)
    return InvitationOut(**data)

@router.delete("/{invitation_id}", response_model=StatusOkResponse)
def delete_invitation(invitation_id: int, user_id: str = Depends(get_current_user)):
    res = delete_invitation_(user_id, invitation_id)
    return StatusOkResponse(**res.json) if hasattr(res, 'json') else StatusOkResponse(**res)

@router.get("/users/invitations", response_model=InvitationListResponse)
def check_user_invitations(user_id: str = Depends(get_current_user)):
    data = check_user_invitations_(user_id)
    return InvitationListResponse(data=[InvitationOut(**inv) for inv in data])

@router.post("/{invitation_id}/ignore", response_model=StatusOkResponse)
def ignore_invitation(invitation_id: int, user_id: str = Depends(get_current_user)):
    res = ignore_invitation_(user_id, invitation_id)
    return StatusOkResponse(**res.json) if hasattr(res, 'json') else StatusOkResponse(**res)