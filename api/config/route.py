# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends, Body
from api.schemas.common import ConfigCreate, ConfigUpdate

from api.config.services import (
    get_user_config_,
    get_config_,
    add_config_,
    edit_config_,
    delete_config_,
    get_config_types_,
)
from dependencies import get_current_user
from models.models import User

# Створюємо Router замість Blueprint
router = APIRouter(tags=["config"])


@router.get("/api/config/config_types")
async def get_config_types():
    """
    Отримання списку типів конфігурації
    """
    return get_config_types_()


@router.get("/api/users/config")
async def get_user_config(current_user: User = Depends(get_current_user)):
    """
    Отримання конфігурації користувача
    """
    return get_user_config_(current_user.id)


@router.post("/api/users/config")
async def add_config(
    config_data: ConfigCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Додавання користувацької конфігурації
    """
    return add_config_(current_user.id, config_data.model_dump())


@router.delete("/api/config/{config_id}")
async def delete_config(
    config_id: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Видалення конфігурації
    """
    return delete_config_(config_id)


@router.patch("/api/config/{config_id}")
async def edit_config(
    config_id: int, 
    config_data: ConfigUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Редагування конфігурації
    """
    return edit_config_(config_id, config_data.model_dump(exclude_unset=True))


@router.get("/api/config/{config_id}")
async def get_config(
    config_id: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Отримання конфігурації за ID
    """
    return get_config_(config_id)
