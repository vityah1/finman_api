# _*_ coding:UTF-8 _*_
import logging
import datetime
import requests

from flask import request, abort, current_app
from api.config.schemas import ConfigTypes

from config import mono_api_url
from api.mono.funcs import (
    _mcc,
    get_mono_user,
    process_mono_data_pmts,
    get_category_id,
    add_new_mono_payment,
    get_mono_user_token,
)
from func import send_telegram
from api.config.services import get_user_config_


mono_logger = logging.getLogger('mono')


def get_mono_user_info_(mono_user_id: int):
    """
    get current webhook from mono
    """
    mono_user_token = None
    result = {}

    mono_user_token = get_mono_user_token(mono_user_id)

    if not mono_user_token:
        current_app.logger.error(f'Token not found. mono_user_id: {mono_user_id}')
        abort(401, f'Token not found. mono_user_id:{mono_user_id}')

    header = {"X-Token": mono_user_token}

    url = f"{mono_api_url}/personal/client-info"

    try:
        r = requests.get(url, headers=header)
    except Exception as err:
        current_app.logger.error(f"{err}")
        abort(400, f'Bad request: {err}\n{r.text}')

    result = r.json()
    result['this_api_webhook'] = request.url_root + f'/api/mono/users/{mono_user_id}/webhook'
    result['mono_user_id'] = mono_user_id

    return result


def set_webhook_(mono_user_id: int):
    """
    set a new webhook for mono user
    """

    mono_token = get_mono_user_token(mono_user_id)
    mono_webhook = request.url_root + f'/api/mono/users/{mono_user_id}/webhook'
    url = f"{mono_api_url}/personal/webhook"

    header = {"X-Token": mono_token}
    data = {"webHookUrl": mono_webhook}

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

    try:
        data = request.get_json()

        mono_logger.info(f'\n{data}\n')
 
        account = data["data"]["account"]
        id = data["data"]["statementItem"]["id"]
        rdate_mono = data["data"]["statementItem"]["time"]
        rdate = datetime.datetime.fromtimestamp(rdate_mono)
        dt = f"{rdate:%d.%m.%Y %H:%M:%S}"
        description = data["data"]["statementItem"]["description"].replace("'", "")
        mcc = data["data"]["statementItem"]["mcc"]
        amount = data["data"]["statementItem"]["amount"]
        # operationAmount = data["data"]["statementItem"]["operationAmount"]
        currencyCode = data["data"]["statementItem"]["currencyCode"]
        balance = data["data"]["statementItem"]["balance"]
        # hold = data["data"]["statementItem"]["hold"]
        if "comment" in data["data"]["statementItem"]:
            comment = data["data"]["statementItem"]["comment"].replace("'", "")
        else:
            comment = ""

    except Exception as err:
        current_app.logger.error(f'{err}')
        abort(422, "Not valid data")

    user_id = 999999

    try:
        mono_user = get_mono_user(mono_user_id)
        user_id = mono_user.user_id

        category_name = _mcc(mcc)
        msg = []
        msg.append(
            f"""<b>{category_name}</b>
user: {mono_user.user.login}
time: {dt}
description: {description} {comment}
mcc: {mcc}
amount: {amount / 100:.2f}
currencyCode: {currencyCode}
balance: {balance}
"""
    )

        is_deleted = 0
        category_id = None
        user_config = mono_user.user.config
        for config_row in user_config:
            # set as deleted according to rules
            if config_row.type_data == ConfigTypes.IS_DELETED_BY_DESCRIPTION.value:
                if description.find(config_row.value_data) > -1:
                    is_deleted = 1
            # for replace category according to rules
            if config_row.type_data == ConfigTypes.CATEGORY_REPLACE.value:
                if config_row.add_value and description.find(config_row.value_data) > -1:
                    try:
                        category_id, description = int(config_row.add_value), category_name
                        comment = description
                        break
                    except Exception as err:
                        mono_logger.warning('can not set category id for cat: {cat}')

        if not category_id:
            category_id = get_category_id(user_id, category_name)

        data_ = {
            'category_id': category_id, 'description': comment,
            'amount': -1 * amount, 'currencyCode': currencyCode, 'mcc': mcc,
            'rdate': rdate, 'type_payment': 'card', 'bank_payment_id': id,
            'user_id': user_id, 'source': 'mono', 'account': account,
            'mono_user_id': mono_user_id, 'is_deleted': is_deleted
        }

        if amount < 0:
            result = add_new_mono_payment(data_)

            if not result:
                msg.append("\nAdd mono webhook <b>FAILED</b>")
            else:
                msg.append(f"\nAdd mono webhook Ok. [{result.id}]")

        send_telegram(user_id, "".join(msg))
        return {"status": "ok"}
    except Exception as err:
        current_app.logger.error(f'{err}')
        send_telegram(user_id, f'Add mono webhook failed...\n{err}')
        abort(200, str(err))


def get_mono_data_pmts_():
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

    user = input_data.get('user')
    if not user:
        current_app.logger.error(f'bad request: {err}')
        abort(400, 'Bad request')

    start_date = input_data.get('start_date')
    end_date = input_data.get('end_date')

    if request.method == 'GET':
        return process_mono_data_pmts(start_date, end_date, user)
    return process_mono_data_pmts(start_date, end_date, user, 'import')
