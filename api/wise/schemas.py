from datetime import datetime
from pydantic import BaseModel

class PaymentData(BaseModel):
    rdate: datetime
    category_id: int
    mydesc: str
    amount: int
    currencyCode: int
    type_payment: str
    bank_payment_id: str | None
    user_id: int
    source: str
