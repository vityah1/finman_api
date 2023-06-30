# _*_ coding:UTF-8 _*_
import logging
from os import abort
import time
import datetime

from pandas import read_excel, read_csv

from mydb import db
from models.models import Payment, User
from .schemas import PaymentData
from api.mono.funcs import find_category
from api.payments.funcs import create_bank_payment_id


logger = logging.getLogger()


def convert_dates(start_date: str = None, end_date: str = None):
    if not start_date:
        start_date = datetime.datetime.today().strftime("%d.%m.%Y") + " 00:00:01"
    elif len(start_date) < 11:
        start_date += " 00:00:01"

    if not end_date:
        end_date = datetime.datetime.today().strftime("%d.%m.%Y") + " 23:59:59"
    elif len(end_date) < 11:
        end_date += " 23:59:59"

    start_date_unix = int(time.mktime(datetime.datetime.strptime(start_date, "%d.%m.%Y %H:%M:%S").timetuple()))
    end_date_unix = int(time.mktime(datetime.datetime.strptime(end_date, "%d.%m.%Y %H:%M:%S").timetuple()))
    return start_date_unix, end_date_unix


def convert_file_to_pmts(user_id: int, file) -> dict:
    data_ = []
    user = db.session.query(User).get(user_id)
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
            rdate=data["Started Date"],
            category_id=find_category(user, data["Description"]),
            mydesc=data["Description"].replace("'", ""),
            amount=amount,
            currencyCode=currencyCode,
            type_payment="card",
            source="revolut",
        )
        pmt_data.bank_payment_id = create_bank_payment_id(pmt_data.dict())
        data_.append(pmt_data.dict())

    return data_


def add_revolut_bulk_payments(data: list[PaymentData]):
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