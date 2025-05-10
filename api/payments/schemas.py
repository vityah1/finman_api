from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date

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
    rdate: Optional[date] = Field(None, description="Дата платежу")

    model_config = {
        "from_attributes": True
    }

class PaymentCreate(PaymentBase):
    bank_payment_id: Optional[str] = Field(None, description="Унікальний ID платежу (генерується автоматично)")
    refuel_data: Optional[RefuelData] = Field(None, description="Дані про заправку (якщо це заправка)")
    user_id: Optional[int] = Field(None, description="ID користувача (встановлюється автоматично)")

class PaymentUpdate(BaseModel):
    amount: Optional[float] = Field(None, description="Сума платежу")
    currency_amount: Optional[float] = Field(None, description="Сума платежу в оригінальній валюті")
    description: Optional[str] = Field(None, description="Опис платежу")
    mydesc: Optional[str] = Field(None, description="Додатковий опис")
    category_id: Optional[int] = Field(None, description="ID категорії")
    currency: Optional[str] = Field(None, description="Валюта платежу")
    rdate: Optional[date] = Field(None, description="Дата платежу")
    refuel_data: Optional[RefuelData] = Field(None, description="Дані про заправку (якщо це заправка)")
    
    model_config = {
        "from_attributes": True
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
