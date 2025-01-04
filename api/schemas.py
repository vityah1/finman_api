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
