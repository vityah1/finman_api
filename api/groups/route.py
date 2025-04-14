# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user

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

@router.patch("/{group_id}/users/{user_id}")
def update_user_relation(group_id: int, user_id: int, user_id_current: str = Depends(get_current_user)):
    return update_user_relation_(user_id_current, group_id, user_id)


@router.get("/{group_id}/invitations")
def get_group_invitations(group_id: int, user_id: str = Depends(get_current_user)):
    return get_group_invitations_(user_id, group_id)


@router.post("/{group_id}/invitations")
def create_group_invitation(group_id: int, user_id: str = Depends(get_current_user)):
    return create_group_invitation_(user_id, group_id)


@router.get("")
def get_groups(user_id: str = Depends(get_current_user)):
    return get_groups_(user_id)


@router.post("")
def create_group(user_id: str = Depends(get_current_user)):
    return create_group_(user_id)


@router.delete("/{group_id}")
def delete_group(group_id: int, user_id: str = Depends(get_current_user)):
    return delete_group_(user_id, group_id)


@router.patch("/{group_id}")
def update_group(group_id: int, user_id: str = Depends(get_current_user)):
    return update_group_(user_id, group_id)


@router.get("/{group_id}")
def get_group(group_id: int, user_id: str = Depends(get_current_user)):
    return get_group_(user_id, group_id)


@router.get("/{group_id}/users")
def get_group_users(group_id: int, user_id: str = Depends(get_current_user)):
    return get_group_users_(user_id, group_id)


@router.post("/{group_id}/users")
def add_user_to_group(group_id: int, user_id: str = Depends(get_current_user)):
    return add_user_to_group_(user_id, group_id)


@router.delete("/{group_id}/users/{user_id_to_remove}")
def remove_user_from_group(group_id: int, user_id_to_remove: int, user_id: int = Depends(get_current_user)):
    """
    remove user from group
    """
    return remove_user_from_group_(user_id, group_id, user_id_to_remove)