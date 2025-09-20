from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime

# Схема для даних про заправку
class RefuelData(BaseModel):
    km: Optional[str] = Field(None, description="Пробіг у кілометрах")
    litres: Optional[str] = Field(None, description="Кількість літрів палива")
    price_val: Optional[str] = Field(None, description="Ціна за літр палива (в EUR)")
    station_name: Optional[str] = Field(None, description="Назва заправки")

# Створюємо Pydantic моделі для запитів та відповідей
class PaymentBase(BaseModel):
    amount: Optional[float] = Field(None, description="Сума платежу")
    currency_amount: Optional[float] = Field(None, description="Сума платежу в оригінальній валюті")
    description: Optional[str] = Field(None, description="Опис платежу")
    mydesc: Optional[str] = Field(None, description="Додатковий опис (автоматично генерується для заправки)")
    category_id: Optional[int] = Field(None, description="ID категорії")
    currency: str = Field("UAH", description="Валюта платежу")
    rdate: Optional[datetime] = Field(None, description="Дата платежу")
    source: Optional[str] = Field(None, description="Джерело платежу (mono, p24, revolut, wise, webapp)")
    refuel_data: Optional[RefuelData] = Field(None, description="Дані про заправку (якщо це заправка)")
    # New currency tracking fields
    amount_original: Optional[float] = Field(None, description="Original amount in transaction currency")
    currency_original: Optional[str] = Field("UAH", description="Original transaction currency")
    exchange_rate: Optional[float] = Field(1.0, description="Exchange rate at transaction time")

    model_config = {
        "from_attributes": True
    }
    
    

class PaymentCreate(PaymentBase):
    bank_payment_id: Optional[str] = Field(None, description="Унікальний ID платежу (генерується автоматично)")
    user_id: Optional[int] = Field(None, description="ID користувача (встановлюється автоматично)")

class PaymentUpdate(PaymentBase):
    # Перевизначаємо поле rdate з іншим типом
    rdate: Optional[date] = Field(None, description="Дата платежу")
    # Всі інші поля успадковуються з PaymentBase
    
    model_config = {
        "from_attributes": True,
        "extra": "ignore"  # Ігнорувати додаткові поля, які не повинні оновлюватися
    }

class PaymentCategoryUpdate(BaseModel):
    payment_ids: List[int] = Field(..., description="Список ID платежів")
    category_id: int = Field(..., description="ID нової категорії")

class PaymentBulkDelete(BaseModel):
    payment_ids: List[int] = Field(..., description="Список ID платежів для видалення")


# Модель для відповіді з платежами
class PaymentResponse(PaymentBase):
    id: Optional[int] = None
    category_name: Optional[str] = None
    user_id: Optional[int] = None
    user_login: Optional[str] = None
    refuel_data: Optional[RefuelData] = None
    mono_user_name: Optional[str] = None
    source: Optional[str] = None

# Модель для відповіді з результатом операції
class OperationResult(BaseModel):
    status: str = "ok"
    detail: Optional[str] = None

class BulkOperationResult(OperationResult):
    count: int = 0
    
    @classmethod
    def success(cls, count: int, operation: str = "") -> dict:
        detail = f"{operation} {count} записів" if operation else None
        return cls(status="ok", count=count, detail=detail).model_dump()
