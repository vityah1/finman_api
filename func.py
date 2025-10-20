import logging
import random
import datetime
import requests
from sqlalchemy import and_

from api.config.schemas import ConfigTypes
from fastapi_sqlalchemy import db
from models import Config

tel_logger = logging.getLogger('telegram')


def get_telegram_data(user_id: int) -> str:
    telegram_token = None
    telegram_chat_id = None
    telegram_data = db.session.query(
        Config.type_data,
        Config.value_data
    ).filter(
        and_(
            Config.user_id == user_id,
            Config.type_data.in_(
                (
                    ConfigTypes.TELEGRAM_TOKEN.value,
                    ConfigTypes.TELEGRAM_CHAT_ID.value,
                )
            )
        )
    ).all()

    for row in telegram_data:
        if row.type_data == ConfigTypes.TELEGRAM_TOKEN.value:
            telegram_token = row.value_data
        elif row.type_data == ConfigTypes.TELEGRAM_CHAT_ID.value:
            telegram_chat_id = row.value_data
    return telegram_token, telegram_chat_id


def mydatetime(par: str = None):
    if not par:
        return datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y %H:%M:%S")
    else:
        return datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d_%H%M%S")


def send_telegram(
        user_id: int,
        text: str,
):
    telegram_token, telegram_chat_id = get_telegram_data(user_id)
    if not any([telegram_token, telegram_chat_id]):
        tel_logger.error(f"""
error send telegram message.
telegram_token or telegram_chat_id for user_id: {user_id} not found
"""
        )
        return 404, ''

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    data = {
        "chat_id": telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "True",
    }

    r = requests.post(url, data=data)

    status_code, content = str(r.status_code), r.reason

    if status_code != 200:
        tel_logger.error(f"""
error send:\nstatus_code: {status_code}, content:{content}
url:{url}
data:{data}\n\n"""
    )

    return status_code, content


rand = random.random() * 10000000
