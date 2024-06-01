# _*_ coding:UTF-8 _*_
import logging

from models.models import User
from api.payments.funcs import create_bank_payment_id
from api.funcs import find_category, get_last_rate
from api.schemas import PaymentData

logger = logging.getLogger()


def revolut_to_pmt(user: User, data) -> PaymentData | None:
    if data["Amount"] > 0:
        return None

    try:
        amount = data["Amount"] * -1 * get_last_rate(data["Currency"], data["Started Date"])
    except Exception as err:
        logger.error(f"{err}")
        amount = 0

    description = data["Description"]
    category_id, is_deleted = find_category(user, description)

    pmt = PaymentData(
        user_id=user.id,
        rdate=data["Started Date"],
        category_id=category_id,
        mydesc=description.replace("'", ""),
        amount=amount,
        currency=data["Currency"],
        type_payment="card",
        source="revolut",
        currency_amount=data["Amount"] * -1,
        is_deleted=is_deleted,
    )

    pmt.bank_payment_id = create_bank_payment_id(pmt.dict())
    return pmt
