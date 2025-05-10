# _*_ coding:UTF-8 _*_
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from pydantic import BaseModel, Field

from api.sprs.services import (
    get_spr_dictionary,
)
from dependencies import get_current_user
from models.models import User

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["sprs"])


@router.get("/api/sprs/{dictionary}")
async def get_dict(
    dictionary: str = Path(..., description="Назва довідника")
):
    """
    Отримання даних довідника
    """
    return get_spr_dictionary(dictionary)
