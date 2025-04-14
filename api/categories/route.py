# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from pydantic import BaseModel
from typing import Optional, List

from api.categories.services import (
    get_categories_,
    add_category_,
    edit_category_,
    delete_category_,
    get_category_,
)


router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    ord: Optional[int] = None
    is_visible: Optional[bool] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    is_fuel: Optional[bool] = None

class CategoryListResponse(BaseModel):
    data: List[CategoryOut]

class CategoryResponse(BaseModel):
    data: CategoryOut

class StatusOkResponse(BaseModel):
    result: str


@router.get("", response_model=CategoryListResponse)
def get_categories(user_id: str = Depends(get_current_user)):
    cats = get_categories_(user_id)
    return CategoryListResponse(data=[CategoryOut(**cat) for cat in cats])


@router.post("", response_model=CategoryResponse)
def add_category(user_id: str = Depends(get_current_user)):
    cat = add_category_(user_id)
    return CategoryResponse(data=CategoryOut(**cat))


@router.delete("/{category_id}", response_model=StatusOkResponse)
def delete_category(category_id: int, user_id: str = Depends(get_current_user)):
    res = delete_category_(category_id)
    return StatusOkResponse(**res)


@router.patch("/{category_id}", response_model=CategoryResponse)
def edit_category(category_id: int, user_id: str = Depends(get_current_user)):
    cat = edit_category_(user_id, category_id)
    return CategoryResponse(data=CategoryOut(**cat))


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, user_id: str = Depends(get_current_user)):
    cat = get_category_(category_id)
    return CategoryResponse(data=CategoryOut(**cat))
