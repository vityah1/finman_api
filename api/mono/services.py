# _*_ coding:UTF-8 _*_
import logging
import requests
from fastapi import HTTPException

from app.config import MONO_API_URL

from api.mono_users.services import get_mono_users_

from api.mono.funcs import (
    process_mono_payments,
    add_new_payment,
    get_mono_user_token,
    convert_webhook_mono_to_payment,
    get_mono_user_info__,
    get_mono_user,
)
from func import send_telegram


mono_logger = logging.getLogger('mono')


def get_mono_user_info_(mono_user_id: int) -> dict:
    """
    Отримати поточний webhook від Mono
    
    Параметри:
        mono_user_id: Ідентифікатор користувача Mono
    """
    return get_mono_user_info__(mono_user_id)


def get_mono_users_info_(user_id: int) -> list[dict]:
    """
    Отримати інформацію про всіх користувачів Mono
    
    Параметри:
        user_id: Ідентифікатор користувача
    """
    result = []
    for mono_user in get_mono_users_(user_id):
        result.append(get_mono_user_info_(mono_user.get('id')))

    return result


def set_webhook_(mono_user_id: int, webhook_url: str) -> dict:
    """
    set a new webhook for mono user
    """
    mono_web_hook_url = webhook_url
    mono_token = get_mono_user_token(mono_user_id)
    # mono_webhook = request.url_root + f'/api/mono/users/{mono_user_id}/webhook'

    url = f"{MONO_API_URL}/personal/webhook"

    header = {"X-Token": mono_token}
    data = {"webHookUrl": mono_web_hook_url}
    # return {'status': 'ok', 'data': data}
    r = None
    try:
        r = requests.post(url, json=data, headers=header)
    except Exception as err:
        mono_logger.error(f"{err}")
        raise HTTPException(400, f'Bad request: {err}\n{r.text if r else ""}')

    return {"status_code": r.status_code, "data": r.text}


def mono_webhook_handler_(mono_user_id: int, webhook_data: dict):
    """
    insert a new webhook from mono
    """
    result = "failed"
    user_id = None
    try:
        mono_logger.info(webhook_data)
        mono_user = get_mono_user(mono_user_id)
        if not mono_user:
            mono_logger.error(f'mono_user_id {mono_user_id} not found')
            raise Exception("mono user not found")
        user_id = mono_user.user_id
        data_ = convert_webhook_mono_to_payment(mono_user, webhook_data)
        if not data_:
            mono_logger.error('Not valid data')
            raise Exception("Not valid data")

        msg = [f"""<b>{data_['category_name']}</b>
user: {mono_user.name}
time: {data_['rdate']:%H:%M:%S}
description: {data_['mydesc']}
mcc: {data_['mcc']}
amount: {data_['amount']}
currencyCode: {data_['currencyCode']}
balance: {data_['balance']}
"""]

        if data_['amount'] > 0:
            payment = add_new_payment(data_)

            if not payment:
                msg.append("\nAdd mono webhook <b>FAILED</b>")
            else:
                msg.append(f"\nAdd mono webhook Ok. [{payment.id=}]")
                result = "ok"

        send_telegram(user_id, "".join(msg))

    except Exception as err:
        mono_logger.error(f'{err}')
        if user_id:
            send_telegram(user_id, f'Add mono webhook failed...\n{err}')
    return {"status": result}


def process_mono_data_payments(user_id: int, input_data: dict):

    mono_user_id = input_data.get('mono_user_id')
    start_date = input_data.get('from_date')
    end_date = input_data.get('to_date')
    mode = input_data.get('mode')

    if mode == 'show':
        return process_mono_payments(user_id, start_date, end_date, mono_user_id, 'show')
    elif mode == 'import':
        return process_mono_payments(user_id, start_date, end_date, mono_user_id, 'import')
    elif mode == 'sync':
        return process_mono_payments(user_id, start_date, end_date, mono_user_id, 'sync')
    else:
        mono_logger.error(f'bad request: invalid import mode: [{mode}]')
        raise HTTPException(400, 'Bad request')
