from fastapi import Depends, HTTPException, status, Header
from typing import Optional
import logging

from sqlalchemy.orm import Session
from mydb import get_db
from models.models import User
from app.auth.jwt import decode_token

logger = logging.getLogger(__name__)

async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    """
    Функція для отримання поточного авторизованого користувача на основі JWT токена
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Відсутній токен авторизації",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    try:
        # Перевіряємо, чи токен має формат 'Bearer <token>'
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неправильний формат токена авторизації",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Декодуємо JWT токен
        user_data = decode_token(token)
        
        # Отримуємо ID користувача
        user_id = user_data.get('user_id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний токен",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Перевіряємо, чи дійсно такий користувач існує
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний користувач",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        return user
    except ValueError:
        # Помилка при розбитті токена (не формат 'Bearer <token>')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний формат токена авторизації",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Помилка автентифікації: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний токен або помилка аутентифікації",
            headers={"WWW-Authenticate": "Bearer"}
        )
