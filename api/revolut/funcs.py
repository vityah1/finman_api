# _*_ coding:UTF-8 _*_
import logging
from typing import Any

from flask import abort, g
from pandas import read_excel, read_csv

from mydb import db
from models.models import User
from .schemas import PaymentData
from api.mono.funcs import find_category
from api.payments.funcs import create_bank_payment_id
from ..funcs import get_last_rate

logger = logging.getLogger()


def convert_file_to_data(user_id: int, file) -> list[dict[str, Any]]:
    revolut_data = []
    session = g.get('db_session', None)
    user: User = session.query(User).get(user_id)
    user_config = user.config

    if file.filename.find('.xls') > 0:
        df = read_excel(file)
    elif file.filename.find('.csv') > 0:
        df = read_csv(
            file,
            delimiter=';',
            parse_dates=['Started Date', 'Completed Date'],
            date_format='%d.%m.%Y %H:%M',
        )
    else:
        abort(400, f'Unknown file type: {file.filename}')

    for index, data in df.iterrows():
        if data["Amount"] > 0:
            continue

        try:
            amount = data["Amount"] * -1 * get_last_rate(data["Currency"], data["Started Date"])
        except Exception as err:
            logger.error(f"{err}")
            amount = 0

        pmt_data = PaymentData(
            user_id=user.id,
            rdate=data["Started Date"],
            category_id=find_category(user, data["Description"]),
            mydesc=data["Description"].replace("'", ""),
            amount=amount,
            currency=data["Currency"],
            type_payment="card",
            source="revolut",
            currency_amount=data["Amount"] * -1,
        )

        pmt_data.bank_payment_id = create_bank_payment_id(pmt_data.dict())
        revolut_data.append(pmt_data.dict())

    return revolut_data
