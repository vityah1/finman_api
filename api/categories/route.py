# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user

from api.categories.services import (
    get_categories_,
    add_category_,
    edit_category_,
    delete_category_,
    get_category_,
)


router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories(user_id: str = Depends(get_current_user)):
    return get_categories_(user_id)


@router.post("")
def add_category(user_id: str = Depends(get_current_user)):
    return add_category_(user_id)


@router.delete("/{category_id}")
def delete_category(category_id: int, user_id: str = Depends(get_current_user)):
    return delete_category_(category_id)


@router.patch("/{category_id}")
def edit_category(category_id: int, user_id: str = Depends(get_current_user)):
    return edit_category_(user_id, category_id)


@router.get("/{category_id}")
def get_category(category_id: int, user_id: str = Depends(get_current_user)):
    return get_category_(category_id)
