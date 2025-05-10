from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
import traceback

from sqlalchemy.orm import Session
from mydb import get_db
from models.models import User
from app.auth.jwt import decode_token

logger = logging.getLogger(__name__)

# Створюємо схеми автентифікації
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")
security = HTTPBearer()

# Функція для отримання токену
async def get_token(authorization: str = Header(None), credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Отримання токену автентифікації з різних джерел
    """
    token = None
    
    # Спробуємо отримати токен з різних джерел
    if credentials:
        # Варіант 1: токен з HTTPBearer
        token = credentials.credentials
        logger.info(f"Token from HTTPBearer: {token[:10]}...")
    elif authorization:
        try:
            # Варіант 2: заголовок Authorization з форматом "Bearer token"
            scheme, value = authorization.split()
            if scheme.lower() == "bearer":
                token = value
                logger.info(f"Token from Authorization header: {token[:10]}...")
        except ValueError:
            # Неправильний формат заголовка
            logger.warning(f"Invalid Authorization header format: {authorization}")
            pass
    
    if not token:
        logger.warning("No valid token found in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Відсутній токен авторизації",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    return token

async def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db)) -> User:
    """
    Функція для отримання поточного авторизованого користувача на основі JWT токена
    """
    try:
        # Декодуємо JWT токен
        user_data = decode_token(token)
        logger.info(f"Decoded user data: {user_data}")
        
        # Отримуємо ID користувача
        user_id = user_data.get('user_id')
        if not user_id:
            logger.warning("No user_id in token data")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний токен",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Перевіряємо, чи дійсно такий користувач існує
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User with id {user_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний користувач",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(f"User authenticated: {user.id}")
        return user
    except Exception as e:
        logger.error(f"Помилка автентифікації: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний токен або помилка аутентифікації",
            headers={"WWW-Authenticate": "Bearer"}
        )
