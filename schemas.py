from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import date, datetime

# Загальні схеми
class ResponseModel(BaseModel):
    status: str
    data: Any

# Схеми для користувачів
class UserBase(BaseModel):
    login: str
    fullname: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class User(UserInDB):
    accessToken: Optional[str] = None

# Схеми для платежів
class PaymentBase(BaseModel):
    amount: float
    description: Optional[str] = None
    category_id: Optional[int] = None
    user_id: int
    currency: str = "UAH"
    rdate: Optional[date] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(PaymentBase):
    amount: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    user_id: Optional[int] = None
    currency: Optional[str] = None
    rdate: Optional[date] = None

class PaymentInDB(PaymentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Payment(PaymentInDB):
    pass

# Схеми для категорій
class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = 0
    user_id: int

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    user_id: Optional[int] = None

class CategoryInDB(CategoryBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Category(CategoryInDB):
    pass
