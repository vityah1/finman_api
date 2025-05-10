# _*_ coding:UTF-8 _*_
import logging
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query, UploadFile, Form
from pydantic import BaseModel, Field

from api.services import bank_import
from dependencies import get_current_user
from models.models import User

# Pydantic моделі для запитів та відповідей
class RevolutImportRequest(BaseModel):
    from_date: Optional[str] = Field(None, description="Початкова дата для імпорту (формат: YYYY-MM-DD)")
    to_date: Optional[str] = Field(None, description="Кінцева дата для імпорту (формат: YYYY-MM-DD)")
    account_id: Optional[str] = Field(None, description="ID рахунку Revolut")

# Створюємо маршрути замість Blueprint
router = APIRouter(tags=["revolut"])

logger = logging.getLogger()


@router.post("/api/revolut/import", status_code=status.HTTP_200_OK)
async def revolut_import(
    file: UploadFile,
    action: str = Form("import"),
    current_user: User = Depends(get_current_user)
):
    """
    Імпорт даних з Revolut через завантаження файлу
    """
    # Викликаємо асинхронну функцію імпорту
    return await bank_import(current_user.id, 'revolut', file, action)
