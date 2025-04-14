import logging
import datetime
from pandas import Series

from models.models import User
from app.api.payments.schemas import PaymentCreate

logger = logging.getLogger(__name__)

def wise_to_pmt(user: User, data: Series) -> PaymentCreate:
    if data["Amount"] > 0:
        return None

    current_date = data["Date"] if isinstance(data["Date"], datetime.datetime) else datetime.datetime.strptime(
        data["Date"],
        "%d-%m-%Y"
    )
    
    from app.api.payments.service import find_category, get_last_rate
    
    try:
        amount = data["Amount"] * -1 * get_last_rate(data["Currency"], current_date)
    except Exception as err:
        logger.error(f"{err}")
        amount = 0

    description = data["Merchant"] if isinstance(data["Merchant"], str) else data["Description"]
    category_id, is_deleted = find_category(user, description)
    
    pmt_dict = {
        "rdate": current_date,
        "category_id": category_id,
        "mydesc": description.replace("'", ""),
        "amount": round(amount),
        "currency": data["Currency"],
        "type_payment": "card",
        "source": "wise",
        "bank_payment_id": data["ID"] if "ID" in data else data["TransferWise ID"],
        "currency_amount": float(data["Amount"]) * -1,
        "is_deleted": is_deleted
    }
    
    return PaymentCreate(**pmt_dict) 