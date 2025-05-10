# _*_ coding:UTF-8 _*_
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from pydantic import BaseModel, Field

from api.services import bank_import
from dependencies import get_current_user
from models.models import User

# Створюємо Pydantic моделі для запитів та відповідей
class WiseImportRequest(BaseModel):
    from_date: Optional[str] = Field(None, description="Початкова дата для імпорту (формат: YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="Кінцева дата для імпорту (формат: YYYY-MM-DD)")
    account_id: Optional[str] = Field(None, description="ID рахунку Wise")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["wise"])

logger = logging.getLogger()


@router.post("/api/wise/import", status_code=status.HTTP_200_OK)
async def wise_import(
    import_data: Optional[WiseImportRequest] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """
    Import data from Wise
    """
    params = None
    if import_data:
        params = import_data.dict(exclude_unset=True)
    
    return bank_import(current_user.id, 'wise', params)
