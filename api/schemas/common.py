"""
Загальні схеми моделей для серіалізації
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


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


class ConfigCreate(BaseModel):
    """Схема для створення конфігурації"""
    type_data: str
    value_data: str
    json_data: Optional[Dict[str, Any]] = None
    add_value: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "type_data": "mono_account",
                "value_data": "1234567890",
                "add_value": "optional_value"
            }
        }


class ConfigUpdate(BaseModel):
    """Схема для оновлення конфігурації"""
    type_data: Optional[str] = None
    value_data: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    add_value: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "type_data": "mono_account",
                "value_data": "1234567890",
                "add_value": "optional_value"
            }
        }


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


class SprSourceResponse(ModelResponse):
    """Схема для відповіді з даними джерела платежу"""
    id: Optional[int] = None
    source: Optional[str] = None


class SprTypePaymentResponse(ModelResponse):
    """Схема для відповіді з даними типу платежу"""
    id: Optional[int] = None
    type_payment: Optional[str] = None


class SprCurrencyResponse(ModelResponse):
    """Схема для відповіді з даними валюти"""
    id: Optional[int] = None
    currency: Optional[str] = None
    currencyCode: Optional[int] = None


class SprConfigTypesResponse(ModelResponse):
    """Схема для відповіді з даними типів конфігурації"""
    id: Optional[int] = None
    type_data: Optional[str] = None
    name: Optional[str] = None
    is_multiple: Optional[bool] = None
    is_need_add_value: Optional[bool] = None
    created: Optional[datetime] = None


class UtilityAddressResponse(ModelResponse):
    """Схема для відповіді з даними адреси комунальних служб"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None


class UtilityServiceResponse(ModelResponse):
    """Схема для відповіді з даними комунальної служби"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    address_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    meter_number: Optional[str] = None
    is_active: Optional[bool] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    address: Optional[UtilityAddressResponse] = None


class UtilityTariffResponse(ModelResponse):
    """Схема для відповіді з даними тарифу комунальної служби"""
    id: Optional[int] = None
    service_id: Optional[int] = None
    name: Optional[str] = None
    rate: Optional[float] = None
    subscription_fee: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: Optional[bool] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    service: Optional[UtilityServiceResponse] = None


class UtilityReadingResponse(ModelResponse):
    """Схема для відповіді з даними показників комунальної служби"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    address_id: Optional[int] = None
    service_id: Optional[int] = None
    period: Optional[str] = None
    current_reading: Optional[float] = None
    previous_reading: Optional[float] = None
    consumption: Optional[float] = None
    tariff_id: Optional[int] = None
    amount: Optional[float] = None
    reading_date: Optional[datetime] = None
    is_paid: Optional[bool] = None
    notes: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    address: Optional[UtilityAddressResponse] = None
    service: Optional[UtilityServiceResponse] = None
    tariff: Optional[UtilityTariffResponse] = None


class UtilityAddressCreate(BaseModel):
    """Схема для створення адреси комунальних служб"""
    name: str
    address: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


class UtilityAddressUpdate(BaseModel):
    """Схема для оновлення адреси комунальних служб"""
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class UtilityServiceCreate(BaseModel):
    """Схема для створення комунальної служби"""
    address_id: int
    name: str
    description: Optional[str] = None
    unit: str
    meter_number: Optional[str] = None
    is_active: Optional[bool] = True


class UtilityServiceUpdate(BaseModel):
    """Схема для оновлення комунальної служби"""
    address_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    meter_number: Optional[str] = None
    is_active: Optional[bool] = None


class UtilityTariffCreate(BaseModel):
    """Схема для створення тарифу"""
    service_id: int
    name: str
    rate: float
    subscription_fee: Optional[float] = 0
    currency: Optional[str] = "UAH"
    valid_from: datetime
    valid_to: Optional[datetime] = None
    is_active: Optional[bool] = True


class UtilityTariffUpdate(BaseModel):
    """Схема для оновлення тарифу"""
    name: Optional[str] = None
    rate: Optional[float] = None
    subscription_fee: Optional[float] = None
    currency: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: Optional[bool] = None


class UtilityReadingCreate(BaseModel):
    """Схема для створення показника"""
    address_id: int
    service_id: int
    period: str
    current_reading: float
    previous_reading: Optional[float] = None
    tariff_id: int
    reading_date: Optional[datetime] = None
    is_paid: Optional[bool] = False
    notes: Optional[str] = None


class UtilityReadingUpdate(BaseModel):
    """Схема для оновлення показника"""
    current_reading: Optional[float] = None
    previous_reading: Optional[float] = None
    tariff_id: Optional[int] = None
    reading_date: Optional[datetime] = None
    is_paid: Optional[bool] = None
    notes: Optional[str] = None