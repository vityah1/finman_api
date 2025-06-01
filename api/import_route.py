# _*_ coding:UTF-8 _*_
import logging
from typing import Literal

from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, status

from api.services import bank_import
from dependencies import get_current_user
from models import User

router = APIRouter()
logger = logging.getLogger()


@router.post("/api/import", status_code=status.HTTP_200_OK)
async def import_bank_statement(
    file: UploadFile,
    mode: Literal["wise", "p24", "revolut", "pumb"] = Form(..., description="Тип банку: 'wise', 'p24', 'revolut', 'pumb'"),
    action: str = Form("show", description="Дія: 'show' для перегляду або 'import' для імпорту"),
    current_user: User = Depends(get_current_user)
):
    """
    Універсальний імпорт банківських виписок
    
    Параметри:
        file: Файл з банківськими транзакціями
        mode: Тип банку (wise, p24, revolut, pumb)
        action: Дія - 'show' для попереднього перегляду або 'import' для імпорту даних
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не надано"
        )
        
    # Перевіряємо тип банку
    if mode not in ["wise", "p24", "revolut", "pumb"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Непідтримуваний тип банку: {mode}. Підтримуються: wise, p24, revolut, pumb"
        )
    
    return await bank_import(current_user, mode, file, action)
