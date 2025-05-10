# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from api.categories.services import (
    get_categories_,
    add_category_,
    edit_category_,
    delete_category_,
    get_category_,
)
from dependencies import get_current_user
from models.models import User

# Створюємо Pydantic моделі для запитів та відповідей
class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None
    parent_id: Optional[int] = None

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["categories"])


@router.get("/api/categories")
async def get_categories(current_user: User = Depends(get_current_user)):
    """
    Отримання списку категорій користувача
    """
    return get_categories_(current_user.id)


@router.post("/api/categories", status_code=status.HTTP_201_CREATED)
async def add_category(
    category: CategoryCreate = Body(...), 
    current_user: User = Depends(get_current_user)
):
    """
    Додавання нової категорії
    """
    return add_category_(current_user.id, category_data=category.dict())


@router.delete("/api/categories/{category_id}")
async def delete_category(
    category_id: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Видалення категорії за ID
    """
    return delete_category_(category_id)


@router.patch("/api/categories/{category_id}")
async def edit_category(
    category_id: int, 
    category: CategoryUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Редагування категорії за ID
    """
    return edit_category_(current_user.id, category_id, category_data=category.dict(exclude_unset=True))


@router.get("/api/categories/{category_id}")
async def get_category(
    category_id: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Отримання категорії за ID
    """
    return get_category_(category_id)
