# _*_ coding:UTF-8 _*_
import logging
from typing import Any

from flask import request, abort
from pandas import read_csv, read_excel

from api.core.funcs import p24_to_pmt
from api.core.revolut.funcs import revolut_to_pmt
from api.core.wise.funcs import wise_to_pmt
from api.funcs import add_bulk_payments
from api.mono.funcs import add_new_payment
from models import User
from mydb import db

logger = logging.getLogger()


def bank_import(user_id: int, bank: str):
    """
    import data from wise
    """

    if 'file' not in request.files:
        abort(400, 'No file part in the request')

    file = request.files['file']

    if file.filename == '':
        abort(400, 'No selected file')

    try:
        data_ = convert_file_to_data(user_id, file, bank)
        if not data_:
            logger.error(f'Not valid data')
            raise Exception("Not valid data")
        if request.form['action'] == 'show':
            return data_
        if request.form['action'] == 'import':
            result = add_bulk_payments(data_)
            if result:
                for pmt_row in data_:
                    pmt_row['sql'] = True
            else:
                for pmt_row in data_:
                    result = add_new_payment(pmt_row)
                    if result:
                        pmt_row['sql'] = True
                    else:
                        pmt_row['sql'] = False
        return data_
    except Exception as err:
        logger.error(f'{err}', exc_info=True)
        return {"status": "failed"}


def convert_file_to_data(user_id: int, file: Any, bank: str) -> list[dict[str, Any]]:
    data = []
    user = db.session.query(User).get(user_id)
    user_config = user.config
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

    if df.empty:
        abort(400, f'file {file.filename} is empty')

    for _, row in df.iterrows():

        match bank:
            case 'revolut':
                pmt = revolut_to_pmt(user, row)
            case 'wise':
                pmt = wise_to_pmt(user, row)
            case 'p24':
                pmt = p24_to_pmt(user, row)
            case _:
                pmt = None

        if pmt:
            data.append(pmt.dict())
        else:
            continue

    return data
