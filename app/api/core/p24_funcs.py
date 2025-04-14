import hashlib
import logging
import datetime
from pandas import Series

from models.models import User
from app.api.payments.schemas import PaymentCreate
from app.api.payments.service import find_category

logger = logging.getLogger(__name__)

def p24_to_pmt(user: User, data: Series) -> PaymentCreate:
    if data.iloc[0] == 'Дата':
        return None

    try:
        amount = data.iloc[4] * -1
    except Exception as err:
        logger.error(f"Error: {err}")
        amount = 0

    mydesc = data.iloc[3]
    category_id, is_deleted = find_category(user, data.iloc[1])

    if data.iloc[7] not in ["EUR", "USD", "UAH"]:
        mydesc = data.iloc[3] + f"; {data.iloc[6]}{data.iloc[7]}"
        
    pmt_dict = {
        "rdate": datetime.datetime.strptime(data.iloc[0], "%d.%m.%Y %H:%M:%S"),
        "category_id": category_id,
        "mydesc": mydesc,
        "amount": round(amount),
        "currency": data.iloc[7] if data.iloc[7] in ["EUR", "USD"] else "UAH",
        "type_payment": "card",
        "source": "p24",
        "bank_payment_id": hashlib.md5(str(data).encode()).hexdigest(),
        "currency_amount": float(data.iloc[6]) if data.iloc[7] in ["EUR", "USD"] else data.iloc[4] * -1,
        "is_deleted": is_deleted
    }
    
    return PaymentCreate(**pmt_dict) 