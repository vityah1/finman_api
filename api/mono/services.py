# _*_ coding:UTF-8 _*_
import logging
import time
import requests

from flask import request, abort, current_app

from config import cfg, users, mono_api_url, mono_webhook
from func import send_telegram
from api.mono.funcs import (
    _mcc,
    process_mono_data_pmts,
    get_user_id,
    get_category_id,
    add_new_mono_payment,
)

mono_logger = logging.getLogger('mono')


def get_webhook_(user):
    """
    get current webhook from mono
    """
    token = None
    result = {}

    if not user:
        current_app.logger.error('Not valid data')
        abort(402, 'Not valid data')        

    for user_ in users:
        if user_.get('name') == user:
            token = user_.get("token")
            break

    if not token:
        current_app.logger.error(f'Token not found: {user}')
        abort(401, f'Token not found: {user}')

    header = {"X-Token": token}

    url = f"{mono_api_url}/personal/client-info"

    try:
        r = requests.get(url, headers=header)
    except Exception as err:
        current_app.logger.error(f"{err}")
        abort(400, f'Bad request: {err}\n{r.text}')

    result = r.json()
    result['this_api_webhook'] = request.host_url + 'api/mono/webhook'
    result['user'] = user

    return result


def set_webhook_():
    """
    set a new webhook on mono
    """
    token = None

    try: 
        data = request.get_json()
        user = data['user']
        webhook = data.get('webhook', mono_webhook)
    except Exception as err:
        current_app.logger.error(f"{err}")
        abort(400, f'Not valid data: {err}')

    url = f"""{mono_api_url}/personal/webhook"""

    for user_ in users:
        if user_.get('name') == user:
            token = user_.get("token")
            break
    if not token:
        abort(401, f'Token not found: {user}')

    header = {"X-Token": token}
    data = {"webHookUrl": webhook}

    try:
        r = requests.post(url, json=data, headers=header)
    except Exception as err:
        current_app.logger.error(f"{err}")
        abort(400, f'Bad request: {err}\n{r.text}')

    return {"status_code": r.status_code, "data": r.text}


def mono_webhook_handler_():
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
        dt = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(rdate_mono))
        t2mysql = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rdate_mono))
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

    user = None
    user_id = 999999

    try:
        user_id = get_user_id(account)
        
        cat = _mcc(mcc)
        msg = []
        msg.append(
            f"""<b>{cat}</b>
    user: {mono_account.user.login}
    time: {dt}
    description: {description} {comment}
    mcc: {mcc}
    amount: {amount / 100:.2f}
    currencyCode: {currencyCode}
    balance: {balance}
    """
        )

        is_deleted = 0
        name_rozhid = ""
        for dlt in cfg["isDeleted"]:
            if description.find(dlt[0]) > -1:
                is_deleted = 1
                name_rozhid = dlt[1]
                break

# for replace name cat according to rules
        for cat1 in cfg["Category"]:
            if len(cat1) > 2 and description.find(cat1[2]) > -1:
                cat = cat1[0]
                comment = description
                description = cat1[1]
                break
        
        category_id = get_category_id(user_id, cat)

        data_ = {
            'category_id': category_id, 'description': comment,
            'amount': -1 * amount, 'currencyCode': currencyCode, 'mcc': mcc,
            'rdate': t2mysql, 'type_payment': 'card', 'bank_payment_id': id,
            'user_id': user_id, 'source': 'mono', 'is_deleted': is_deleted
        }

        if amount < 0:
            result = add_new_mono_payment(data_)

            if not result:
                msg.append(f"\nerror. [{res}]\n{sql}")
            else:
                msg.append(f"\ninsert to `payments` Ok. [{result.get('id')}]")

        send_telegram("".join(msg), "HTML", "", "bank")
        return {"status": "ok"}
    except Exception as err:
        current_app.logger.error(f'{err}')
        abort(500, str(err))


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
