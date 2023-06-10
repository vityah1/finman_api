# _*_ coding:UTF-8 _*_
import logging
import requests

from flask import request, abort, current_app
from api.mono_users.services import get_mono_users_

from config import mono_api_url
from api.mono.funcs import (
    process_mono_data_pmts,
    add_new_mono_payment,
    get_mono_user_token,
    convert_mono_to_pmts,
    get_mono_user_info__,
)
from func import send_telegram


mono_logger = logging.getLogger('mono')


def get_mono_user_info_(mono_user_id: int) -> dict:
    """
    get current webhook from mono
    """
    return get_mono_user_info__(mono_user_id)


def get_mono_users_info_(user_id: int) -> list[dict]:
    """
    get all mono users info from mono
    """
    result = []
    for mono_user in get_mono_users_(user_id):
        result.append(get_mono_user_info_(mono_user.get('id')))

    return result


def set_webhook_(mono_user_id: int) -> dict:
    """
    set a new webhook for mono user
    """
    data = request.get_json()
    mono_webHookUrl = data.get('webHookUrl')
    mono_token = get_mono_user_token(mono_user_id)
    # mono_webhook = request.url_root + f'/api/mono/users/{mono_user_id}/webhook'

    url = f"{mono_api_url}/personal/webhook"

    header = {"X-Token": mono_token}
    data = {"webHookUrl": mono_webHookUrl}
    # return {'status': 'ok', 'data': data}

    try:
        r = requests.post(url, json=data, headers=header)
    except Exception as err:
        current_app.logger.error(f"{err}")
        abort(400, f'Bad request: {err}\n{r.text}')

    return {"status_code": r.status_code, "data": r.text}


def mono_webhook_handler_(mono_user_id: int):
    """
    insert a new webhook from mono
    """

    if request.method == 'GET':
        return {'status': 'ok'}

    data = request.get_json()
    data_ = convert_mono_to_pmts(mono_user_id, data)
    if not data_:
        # abort(422, "Not valid data")
        return {'status': 'empty data'}

    msg = []
    msg.append(
        f"""<b>{data_['category_name']}</b>
user: {data_['mono_user_name']}
time: {data_['rdate']}
description: {data_['mydesc']}
mcc: {data_['mcc']}
amount: {data_['amount'] / 100:.2f}
currencyCode: {data_['currencyCode']}
balance: {data_['balance']}
"""
)

    if data_['amount'] > 0:
        result = add_new_mono_payment(data_)

        if not result:
            msg.append("\nAdd mono webhook <b>FAILED</b>")
        else:
            msg.append(f"\nAdd mono webhook Ok. [{result.id}]")

    send_telegram(data_['user_id'], "".join(msg))
    return {"status": "ok"}
    # except Exception as err:
    #     current_app.logger.error(f'{err}')
    #     send_telegram(user_id, f'Add mono webhook failed...\n{err}')
    #     abort(200, str(err))


def get_mono_data_pmts_(user_id: int):
    input_data = {}
    if request.method == 'GET':
        try:
            input_data = dict(request.args)
        except Exception as err:
            current_app.logger.error(f'bad request: {err}')
            abort(400, 'Bad request')
    else:
        try:
            input_data = request.get_json()
        except Exception as err:
            current_app.logger.error(f'bad request: {err}')
            abort(400, 'Bad request')

    mono_user_id = input_data.get('mono_user_id')
    # if not mono_user_id:
    #     current_app.logger.warning(f'user not found in input data:\n{input_data}')
    #     # abort(400, 'Bad request')
    #     mono_user_id = None

    start_date = input_data.get('start_date')
    end_date = input_data.get('end_date')

    if request.method == 'GET':
        return process_mono_data_pmts(user_id, start_date, end_date, mono_user_id)
    return process_mono_data_pmts(user_id, start_date, end_date, mono_user_id, 'import')
