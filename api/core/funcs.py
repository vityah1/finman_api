# _*_ coding:UTF-8 _*_
import hashlib
import logging
import datetime

from pandas import Series

from models.models import User
from api.schemas import PaymentData
from api.funcs import find_category, get_last_rate

logger = logging.getLogger()


def p24_to_pmt(user: User, data: Series) -> PaymentData | None:
    if data.iloc[0] == 'Дата':
        return None

    try:
        amount = data.iloc[4] * -1
    except Exception as err:
        print(f"Error: {err}")
        amount = 0

    mydesc = data.iloc[3]
    category_id, is_deleted = find_category(user, data.iloc[1])

    if data.iloc[7] not in ["EUR", "USD", "UAH"]:
        mydesc = data.iloc[3] + f"; {data.iloc[6]}{data.iloc[7]}"

    return PaymentData(
        user_id=user.id,
        rdate=datetime.datetime.strptime(data.iloc[0], "%d.%m.%Y %H:%M:%S"),
        category_id=category_id,
        mydesc=mydesc,
        amount=round(amount),
        currency=data.iloc[7] if data.iloc[7] in ["EUR", "USD"] else "UAH",
        type_payment="card",
        source="p24",
        bank_payment_id=hashlib.md5(str(data).encode()).hexdigest(),
        currency_amount=float(data.iloc[6]) if data.iloc[7] in ["EUR", "USD"] else data.iloc[
                                                                              4] * -1,
        is_deleted=is_deleted,
    )
