from datetime import datetime
from pydantic import BaseModel


class PaymentData(BaseModel):
    rdate: datetime
    category_id: int
    mydesc: str
    amount: int # value in UAH without cents
    # currencyCode: int | None
    type_payment: str
    bank_payment_id: str | None
    user_id: int
    source: str
    currency_amount: float | None
    currency: str | None
    is_deleted: bool | None = False


class UtilityTypeData(BaseModel):
    name: str
    description: str | None = None
    user_id: int | None = None
    group_id: int | None = None


class UtilityMeterData(BaseModel):
    name: str
    description: str | None = None
    utility_type_id: int
    user_id: int | None = None
    group_id: int | None = None
    is_active: bool = True
    serial_number: str | None = None


class UtilityTariffData(BaseModel):
    name: str
    description: str | None = None
    utility_type_id: int
    rate: float
    currency: str = "UAH"
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    user_id: int | None = None
    group_id: int | None = None
    tariff_type: str | None = None


class UtilityMeterReadingData(BaseModel):
    meter_id: int
    reading_date: datetime | None = None
    reading_value: float
    previous_reading_id: int | None = None
    consumption: float | None = None
    user_id: int | None = None
    group_id: int | None = None
    tariff_id: int | None = None
    image_url: str | None = None
    month: int
    year: int
    cost: float | None = None
