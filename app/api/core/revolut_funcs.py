import logging
from datetime import datetime
from pandas import Series

from models.models import User
from app.api.payments.schemas import PaymentCreate
from app.api.payments.service import find_category, get_last_rate, create_bank_payment_id

logger = logging.getLogger(__name__)

def revolut_to_pmt(user: User, data) -> PaymentCreate:
    if data["Amount"] > 0:
        return None

    try:
        amount = data["Amount"] * -1 * get_last_rate(data["Currency"], data["Started Date"])
    except Exception as err:
        logger.error(f"{err}")
        amount = 0

    description = data["Description"]
    category_id, is_deleted = find_category(user, description)

    pmt_dict = {
        "rdate": data["Started Date"],
        "category_id": category_id,
        "mydesc": description.replace("'", ""),
        "amount": amount,
        "currency": data["Currency"],
        "type_payment": "card",
        "source": "revolut",
        "currency_amount": data["Amount"] * -1,
        "is_deleted": is_deleted
    }
    
    # Створюємо bank_payment_id
    bank_payment_id = create_bank_payment_id(pmt_dict)
    pmt_dict["bank_payment_id"] = bank_payment_id
    
    return PaymentCreate(**pmt_dict) 