"""
Загальні схеми моделей для серіалізації
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    """Базовий клас для всіх відповідей API з моделей БД"""
    
    model_config = {"from_attributes": True}


class UserResponse(ModelResponse):
    """Схема для відповіді з даними користувача"""
    id: Optional[int] = None
    login: Optional[str] = None
    fullname: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created: Optional[datetime] = None
    is_admin: Optional[bool] = None


class CategoryResponse(ModelResponse):
    """Схема для відповіді з даними категорії"""
    id: Optional[int] = None
    name: Optional[str] = None
    parent_id: Optional[int] = None
    ord: Optional[int] = None
    is_visible: Optional[bool] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    is_fuel: Optional[bool] = None


class GroupResponse(ModelResponse):
    """Схема для відповіді з даними групи"""
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    created: Optional[datetime] = None


class MonoUserResponse(ModelResponse):
    """Схема для відповіді з даними користувача Monobank"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: Optional[str] = None
    token: Optional[str] = None
    created: Optional[datetime] = None


class ConfigResponse(ModelResponse):
    """Схема для відповіді з даними конфігурації"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    type_data: Optional[str] = None
    value_data: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    add_value: Optional[str] = None
    created: Optional[datetime] = None


class GroupInvitationResponse(ModelResponse):
    """Схема для відповіді з даними запрошення в групу"""
    id: Optional[int] = None
    group_id: Optional[int] = None
    created_by: Optional[int] = None
    invitation_code: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    created: Optional[datetime] = None
    expires: Optional[datetime] = None
    group: Optional[GroupResponse] = None
    creator: Optional[UserResponse] = None


class PaymentData(BaseModel):
    """Схема для даних про платіж"""
    rdate: datetime
    category_id: int
    mydesc: str
    amount: int  # value in UAH without cents
    type_payment: str
    bank_payment_id: Optional[str] = None
    user_id: int
    source: str
    currency_amount: Optional[float] = None
    currency: Optional[str] = None
    is_deleted: Optional[bool] = False
