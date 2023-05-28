import re

from sqlalchemy import and_

from api.config.schemas import ConfigTypes
from mydb import db
from models import Config


def convert_desc_to_refuel_data(description: str) -> dict:
    refuel_data = {}

    for item in description.split(';'):
        if r := re.search(r'(\d+)км', item):
            refuel_data['km'] = r.group(1)
        elif r := re.search(r'(\d+)л', item):
            refuel_data['litres'] = r.group(1)
        elif r := re.search(r'(\d+(\.)?(\d+)?)eur', item):
            refuel_data['price_val'] = r.group(1)
        else:
            refuel_data['name'] = item

    return refuel_data


def conv_refuel_data_to_desc(data: dict) -> dict:
    result = data.copy()
    if data.get('km') and data.get('litres'):
        result['description'] = '{}км;{}л'.format(data.get('km'), data.get('litres'))
        if data.get('price_val'):
            result['description'] += ';{}eur'.format(data.get('price_val'))
        if data.get('name') or data.get('station'):
            result['description'] += ';{}'.format(
                data.get('name') if data.get('name') else data.get('station')
            )
    return result


def get_user_phones_from_config(user_id: int) -> list[dict]:
    user_phones = {}
    user_config = db.session().query(
        Config.value_data,
        Config.add_value
        ).filter(
            and_(
                Config.user_id == user_id,
                Config.type_data == ConfigTypes.PHONE_TO_NAME,
            )
    ).all()
    for config in user_config:
        user_phones[config.value_data] = config.add_value
    return user_phones



