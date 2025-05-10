from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from jose import jwt, JWTError
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.config import SECRET_KEY


# Налаштування JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 години


class TokenData(BaseModel):
    user_id: Optional[int] = None


def create_access_token(data: Dict[str, Any]) -> str:
    """
    Створення JWT токену для користувача
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Перетворюємо словник в JSON рядок, щоб формат залишався таким самим як раніше
    subject = json.dumps(data)
    
    encoded_jwt = jwt.encode(
        {"sub": subject, "exp": expire}, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Розшифрування JWT токену
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Розшифровуємо JSON рядок з суб'єкта
        user_data = json.loads(subject)
        return user_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
