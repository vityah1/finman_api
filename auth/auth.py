import logging
from datetime import timedelta
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import and_
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.schemas import UserResponse

from utility_helpers import do_sql_cmd
from mydb import get_db
from models import User
from app.auth.jwt import create_access_token
from dependencies import get_current_user

logger = logging.getLogger(__name__)

# Створюємо Router замість Blueprint
router = APIRouter(tags=["auth"])

# Схема OAuth2 для автентифікації
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")

# Пайдантік моделі для запитів та відповідей
class LoginModel(BaseModel):
    login: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "login": "admin",
                "password": "password"
            }
        }
        
class UserCreate(BaseModel):
    login: str
    password: str
    fullname: str = ""
    phone: str = ""
    email: str = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "login": "new_user",
                "password": "password",
                "fullname": "Іванов Іван",
                "phone": "+380991234567",
                "email": "user@example.com"
            }
        }
        
class UserUpdate(BaseModel):
    login: str
    password: str
    fullname: str = ""
    phone: str = ""
    email: str = ""


@router.post("/api/auth/signin", status_code=status.HTTP_200_OK)
async def user_login(login_data: LoginModel, db: Session = Depends(get_db)):
    """
    Автентифікація користувача та отримання JWT токена
    """
    # Шукаємо користувача за логіном та паролем
    user = db.query(User).filter(
        and_(
            User.login == login_data.login,
            User.password == login_data.password
        )
    ).one_or_none()
    
    # Якщо користувача не знайдено - повертаємо помилку
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль"
        )
    
    # Створюємо дані для JWT токена
    user_data = {
        'login': user.login,
        'user_id': user.id
    }
    
    # Створюємо JWT токен доступу з використанням нової функції
    access_token = create_access_token(user_data)
    
    # Формуємо відповідь
    result = UserResponse.model_validate(user).model_dump()
    result['accessToken'] = access_token
    
    return result


@router.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Створення нового користувача
    """
    user = User(**user_data.dict())
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as err:
        db.rollback()
        logger.error(f"Помилка при створенні користувача: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при створенні користувача: {str(err)}"
        )

    # Створюємо об'єкт ідентифікації та перетворюємо його в JSON
    user_identity = json.dumps({
        'login': user.login,
        'user_id': user.id
    })
    
    access_token = Authorize.create_access_token(
        subject=user_identity, 
        expires_time=timedelta(days=45)
    )
    
    # Декодуємо токен якщо він в байтах
    if isinstance(access_token, bytes):
        access_token = access_token.decode('utf-8')
        
    result = UserResponse.model_validate(user).model_dump()
    result["accessToken"] = access_token
    return result


@router.get("/api/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Отримання інформації про користувача за ID
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Користувача не знайдено'
        )

    return UserResponse.model_validate(user).model_dump()


@router.delete("/api/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Видалення користувача за ID
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Користувача не знайдено'
        )
        
    try:
        db.delete(user)
        db.commit()
    except Exception as err:
        db.rollback()
        logger.error(f"Помилка при видаленні користувача: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при видаленні користувача: {str(err)}"
        )

    return {"result": "ok"}


@router.get("/api/users", status_code=status.HTTP_200_OK)
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Отримання списку всіх користувачів (тільки для адміністраторів)
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Доступ заборонено. Тільки адміністратори можуть переглядати список всіх користувачів.'
        )

    users = db.query(User).all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Користувачів не знайдено'
        )

    return [UserResponse.model_validate(user).model_dump() for user in users]


@router.patch("/api/users/{user_id}", status_code=status.HTTP_200_OK)
async def edit_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db)
):
    """
    Оновлення даних користувача
    """
    data = user_data.model_dump()
    data['user_id'] = user_id

    sql = """update `users` 
set login = :login, password = :password, fullname = :fullname, phone = :phone, email = :email 
where id = :user_id """

    res = do_sql_cmd(sql, data)
    if res["rowcount"] < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Помилка при редагуванні користувача"
        )

    # Створюємо дані для JWT токена
    user_data = {
        'login': data.get('login'),
        'user_id': user_id
    }
    
    # Створюємо JWT токен доступу з використанням нової функції
    access_token = create_access_token(user_data)

    return {
        "user_id": user_id,
        "accessToken": access_token,
        "login": data.get('login'),
        "fullname": data.get('fullname'),
        "phone": data.get('phone'),
        "email": data.get('email'),
    }
