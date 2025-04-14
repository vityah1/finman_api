# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from api.invitations.services import (
    check_invitation_, accept_invitation_, check_user_invitations_, delete_invitation_,
    get_invitation_, ignore_invitation_,
)

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


@router.get("/{invitation_code}")
def check_invitation(invitation_code: str, user_id: str = Depends(get_current_user)):
        return check_invitation_(user_id, invitation_code)

@router.post("/{invitation_code}/accept")
def accept_invitation(invitation_code: str, user_id: str = Depends(get_current_user)):
        return accept_invitation_(user_id, invitation_code)

@router.get("/{invitation_id}")
def get_invitation(invitation_id: int, user_id: str = Depends(get_current_user)):
        return get_invitation_(user_id, invitation_id)

@router.delete("/{invitation_id}")
def delete_invitation(invitation_id: int, user_id: str = Depends(get_current_user)):
        return delete_invitation_(user_id, invitation_id)

@router.get("/users/invitations")
def check_user_invitations(user_id: str = Depends(get_current_user)):
        return check_user_invitations_(user_id)

@router.post("/{invitation_id}/ignore")
def ignore_invitation(invitation_id: int, user_id: str = Depends(get_current_user)):
        return ignore_invitation_(user_id, invitation_id)