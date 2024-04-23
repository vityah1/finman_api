import datetime
import hashlib
import re
from datetime import datetime
from pandas import Timestamp

from sqlalchemy import and_

from api.config.schemas import ConfigTypes
from mydb import db
from models import Config


def create_bank_payment_id(data):
    if isinstance(data['rdate'], (Timestamp, datetime)):
        rdate_ = f"{data['rdate']:%Y%m%d%H%M%S}"
    else:
        rdate_ = data['rdate']
    bank_payment_id = f"{rdate_}{data['user_id']}{data['mydesc']}{data['currency_amount']}0"
    hash_object = hashlib.sha256(bank_payment_id.encode())
    bank_payment_id = hash_object.hexdigest()
    return bank_payment_id


def convert_desc_to_refuel_data(mydesc: str) -> dict:
    refuel_data = {}

    for item in mydesc.split(';'):
        if r := re.search(r'(\d+)км', item):
            refuel_data['km'] = r.group(1)
        elif r := re.search(r'(\d+)л', item):
            refuel_data['litres'] = r.group(1)
        elif r := re.search(r'(\d+(\.)?(\d+)?)eur', item):
            refuel_data['price_val'] = r.group(1)
        else:
            refuel_data['station_name'] = item

    return refuel_data


def conv_refuel_data_to_desc(data: dict) -> dict:
    result = ''
    if data.get('km') and data.get('litres'):
        result = '{}км;{}л'.format(data.get('km'), data.get('litres'))
        if data.get('price_val'):
            result += ';{}eur'.format(data.get('price_val'))
        if data.get('station_name'):
            result += ';{}'.format(
                data.get('station_name')
            )
    return result


def get_user_phones_from_config(user_id: int) -> list[dict]:
    user_phones = {}
    user_config = db.session().query(
        Config.value_data,
        Config.add_value,
    ).filter(
        and_(
            Config.user_id == user_id,
            Config.type_data == ConfigTypes.PHONE_TO_NAME.value,
        )
    ).all()
    for config in user_config:
        user_phones[config.value_data] = config.add_value
    return user_phones


def get_dates(month, year):
    current_date = datetime.datetime.now()
    if not year:
        year = f"{current_date:%Y}"
    if not month:
        month = f"{current_date:%m}"
    start_date = f"{year}-{int(month):02d}-01"
    end_date = f"{year if int(month) < 12 else int(year) + 1}-{int(month) + 1 if int(month) < 12 else 1:02d}-01"
    return current_date, end_date, start_date
