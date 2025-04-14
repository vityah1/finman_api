# _*_ coding:UTF-8 _*_
import logging

from fastapi import APIRouter, Depends
from app.jwt import get_current_user

from api.services import bank_import


router = APIRouter(prefix="/api/p24", tags=["p24"])

logger = logging.getLogger()


@router.post("/import")
def p24_import(user_id: str = Depends(get_current_user)):
    return bank_import(user_id, 'p24')
