# _*_ coding:UTF-8 _*_
import logging
from os import abort
import datetime
from typing import Any

from pandas import read_excel, read_csv

from mydb import db
from models.models import Payment, User
from .schemas import PaymentData
from api.mono.funcs import find_category


logger = logging.getLogger()

def convert_file_to_pmts(user_id: int, file) -> list[dict[str, Any]]:
    wise_data = []
    user = db.session.query(User).get(user_id)
    if file.filename.find('.xls') > 0:
        df = read_excel(file)
    elif file.filename.find('.csv') > 0:
        df = read_csv(
            file,
            delimiter=',',
            parse_dates=['Date'],
            date_format='%d-%m-%Y',
        )
    else:
        abort(400, f'Unknown file type: {file.filename}')
    for index, data in df.iterrows():
        if data["Amount"] > 0:
            continue        
        if data["Currency"] == "EUR":
            currencyCode = 978
            amount = data["Amount"] * -1 * 40.60
        elif data["Currency"] == "USD":
            currencyCode = 840
            amount = data["Amount"] * -1 * 37.44
        else:
            continue
        pmt_data = PaymentData(
            user_id=user.id,
            rdate=data["Date"] if isinstance(data["Date"], datetime.datetime) else datetime.datetime.strptime(data["Date"],
                "%d-%m-%Y"),
            category_id=find_category(user, data["Merchant"]),
            mydesc=data["Merchant"].replace("'", ""),
            amount=amount,
            currencyCode=currencyCode,
            type_payment="card",
            source="wise",
            bank_payment_id=data["ID"] if "ID" in data else data["TransferWise ID"],
        )
        wise_data.append(pmt_data.dict())

    return wise_data


def add_wise_bulk_payments(data: list[PaymentData]):
    result = False
    try:
        db.session.bulk_insert_mappings(Payment, data)
        db.session.commit()
        result = True
    except Exception as err:
        logger.error(f'{err}')
        db.session.rollback()
        db.session.flush()
    return result