# _*_ coding:UTF-8 _*_
import datetime
import logging
import random
import time

import requests
from fastapi import HTTPException
from sqlalchemy import and_

from app.config import MONO_API_URL, BASE_URL
from api.config.schemas import ConfigTypes
from api.mono.services import get_mono_users_
from models.models import Category, Config, MonoUser, Payment, User
from fastapi_sqlalchemy import db

mono_logger = logging.getLogger('mono')


def get_config_accounts(mono_user_id: int) -> list[Config.value_data]:
    results = db.session.query(
        Config.value_data
    ).join(
        User
    ).join(
        MonoUser, MonoUser.user_id == User.id
    ).filter(
        MonoUser.id == mono_user_id, Config.type_data == 'mono_account', ).all()
    return [result[0] for result in results]


def get_mono_user_info__(mono_user_id: int,):
    mono_user_token = get_mono_user_token(mono_user_id)

    if not mono_user_token:
        mono_logger.error(f'Token not found. mono_user_id: {mono_user_id}')
        raise HTTPException(401, f'Token not found. mono_user_id:{mono_user_id}')

    header = {"X-Token": mono_user_token}

    url = f"{MONO_API_URL}/personal/client-info"
    r = None
    try:
        r = requests.get(url, headers=header)
    except Exception as err:
        mono_logger.error(f"{err}")
        raise HTTPException(400, f'Bad request: {err}\n{r.text if r else ""}')

    result = r.json()
    result['this_api_webhook'] = BASE_URL + f'/api/mono/users/{mono_user_id}/webhook'
    result['mono_user_id'] = mono_user_id
    result['mono_user_token'] = mono_user_token

    return result


def _mcc(mcc):
    if (mcc in (
            4011, 4111, 4112, 4131, 4304, 4411, 4415, 4418, 4457, 4468, 4511, 4582, 4722, 4784, 4789, 5962, 6513, 7011,
            7032, 7033, 7512, 7513, 7519,) or mcc in range(3000, 4000)):
        return "Подорожі"
    elif (mcc in (
            4119, 5047, 5122, 5292, 5295, 5912, 5975, 5976, 5977, 7230, 7297, 7298, 8011, 8021, 8031, 8049, 8050, 8062,
            8071, 8099,) or mcc in range(8041, 8044)):
        return "Краса та медицина"
    elif (mcc in (5733, 5735, 5941, 7221, 7333, 7395, 7929, 7932, 7933, 7941, 7991, 7995, 8664,) or mcc in range(
        5970, 5974
    ) or mcc in range(5945, 5948) or mcc in range(5815, 5819) or mcc in range(7911, 7923) or mcc in range(
        7991, 7995
    ) or mcc in range(7996, 8000)):
        return "Розваги та спорт"
    elif mcc in range(5811, 5815):
        return "Кафе та ресторани"
    elif mcc in (5297, 5298, 5300, 5311, 5331, 5399, 5411, 5412, 5422, 5441, 5451, 5462, 5499, 5715, 5921,):
        return "Продукти й супермаркети"
    elif mcc in (7829, 7832, 7841):
        return "Кіно"
    elif (mcc in (5172, 5511, 5541, 5542, 5983, 7511, 7523, 7531, 7534, 7535, 7538, 7542, 7549,) or mcc in range(
        5531, 5534
    )):
        return "Авто та АЗС"
    elif mcc in (
            5131, 5137, 5139, 5611, 5621, 5631, 5641, 5651, 5655, 5661, 5681, 5691, 5697, 5698, 5699, 5931, 5948, 5949,
            7251, 7296,):
        return "Одяг і взуття"
    elif mcc == 4121:
        return "Таксі"
    elif mcc in (742, 5995):
        return "Тварини"
    elif mcc in (2741, 5111, 5192, 5942, 5994):
        return "Книги"
    elif mcc in (5992, 5193):
        return "Квіти"
    elif mcc in (4814, 4812):
        return "Поповнення мобільного"
    elif mcc == 4829:
        return "Грошові перекази"
    elif mcc == 4900:
        return "Комунальні послуги"
    else:
        return "Інше"


def convert_dates(start_date: str = None, end_date: str = None):
    # Helper function to detect date format and convert to datetime
    def parse_date(date_str):
        if not date_str:
            return None
        # Try YYYY-MM-DD format first (ISO format from frontend)
        if '-' in date_str and len(date_str.split('-')[0]) == 4:
            try:
                return datetime.datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            except ValueError:
                pass
        # Try DD.MM.YYYY format (old format)
        try:
            return datetime.datetime.strptime(date_str.split()[0], "%d.%m.%Y")
        except ValueError:
            pass
        return None

    # Process start_date
    if not start_date:
        start_dt = datetime.datetime.today().replace(hour=0, minute=0, second=1)
    else:
        start_dt = parse_date(start_date)
        if not start_dt:
            raise ValueError(f"Invalid start_date format: {start_date}")
        # If time is not specified, add 00:00:01
        if len(start_date) < 11:
            start_dt = start_dt.replace(hour=0, minute=0, second=1)

    # Process end_date
    if not end_date:
        end_dt = datetime.datetime.today().replace(hour=23, minute=59, second=59)
    else:
        end_dt = parse_date(end_date)
        if not end_dt:
            raise ValueError(f"Invalid end_date format: {end_date}")
        # If time is not specified, add 23:59:59
        if len(end_date) < 11:
            end_dt = end_dt.replace(hour=23, minute=59, second=59)

    start_date_unix = int(time.mktime(start_dt.timetuple()))
    end_date_unix = int(time.mktime(end_dt.timetuple()))

    return start_date_unix, end_date_unix


def set_category(
        user_id: int, mono_user: MonoUser, mcc: int, description: str
):
    is_deleted = 0
    category_id = None
    category_name = _mcc(mcc)
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
                    break
                except Exception as err:
                    mono_logger.warning(f'can not set category id for cat: {config_row.add_value=}, {err}')

    if not category_id:
        category_id = get_category_id(user_id, category_name)
    return category_id, category_name, is_deleted


def convert_imp_mono_to_payment(user_id: int, mono_user: MonoUser, mono_payment: dict):
    data = {
        'user_id': user_id, 'rdate': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mono_payment["time"])),
        'bank_payment_id': mono_payment["id"], 'mydesc': mono_payment["description"], 'mcc': mono_payment["mcc"],
        'amount': -1 * mono_payment["amount"] / 100, 'currencyCode': mono_payment["currencyCode"]
    }

    # Currency code mapping: 978=EUR, 840=USD, 980=UAH
    currency_map = {978: 'EUR', 840: 'USD', 980: 'UAH', 348: 'HUF', 191: 'HRK', 826: 'GBP', 203: 'CZK'}
    original_currency = currency_map.get(mono_payment["currencyCode"], 'UAH')

    data['currency_amount'] = data['amount']
    data['currency'] = 'UAH'
    data['mono_user_id'] = mono_user.id
    data['source'] = 'mono'
    data['type_payment'] = 'card'
    data['category_id'], data['category_name'], data['is_deleted'] = set_category(
        user_id, mono_user, data['mcc'], data['mydesc']
    )

    # Calculate original amount and exchange rate
    operationAmount = mono_payment.get("operationAmount")
    if operationAmount and mono_payment["currencyCode"] != 980:  # Foreign currency transaction
        # operationAmount is in minor units of original currency (also negative for expenses)
        original_amount = -1 * operationAmount / 100  # Convert to positive like we do with amount
        exchange_rate = abs(data['amount'] / original_amount) if original_amount != 0 else 1.0
    else:
        # UAH transaction or no operationAmount
        original_amount = data['amount']
        exchange_rate = 1.0

    # New currency tracking fields with proper values
    data['amount_original'] = original_amount
    data['currency_original'] = original_currency
    data['exchange_rate'] = exchange_rate

    return data


def convert_webhook_mono_to_payment(mono_user: MonoUser, data: dict) -> dict:

    account = data["data"]["account"]
    id = data["data"]["statementItem"]["id"]
    rdate_mono = data["data"]["statementItem"]["time"]
    rdate = datetime.datetime.fromtimestamp(rdate_mono)
    # dt = f"{rdate:%d.%m.%Y %H:%M:%S}"
    description = data["data"]["statementItem"]["description"].replace("'", "")
    mcc = data["data"]["statementItem"]["mcc"]
    amount = data["data"]["statementItem"]["amount"] / 100
    operationAmount = data["data"]["statementItem"].get("operationAmount")
    currencyCode = data["data"]["statementItem"]["currencyCode"]
    currency = 'UAH'
    balance = data["data"]["statementItem"]["balance"]
    # hold = data["data"]["statementItem"]["hold"]
    if "comment" in data["data"]["statementItem"]:
        description += "; " + data["data"]["statementItem"]["comment"].replace("'", "")

    user_id = mono_user.user_id

    category_id, category_name, is_deleted = set_category(user_id, mono_user, mcc, description)

    # Currency code mapping: 978=EUR, 840=USD, 980=UAH
    currency_map = {978: 'EUR', 840: 'USD', 980: 'UAH', 348: 'HUF', 191: 'HRK', 826: 'GBP', 203: 'CZK'}
    original_currency = currency_map.get(currencyCode, 'UAH')

    # Calculate original amount and exchange rate
    if operationAmount and currencyCode != 980:  # Foreign currency transaction
        # operationAmount is in minor units of original currency
        original_amount = operationAmount / 100
        exchange_rate = abs(amount / original_amount) if original_amount != 0 else 1.0
    else:
        # UAH transaction or no operationAmount
        original_amount = amount
        exchange_rate = 1.0

    data_ = {
        'category_id': category_id, 'mydesc': description, 'amount': -1 * amount, 'currencyCode': currencyCode,
        'mcc': mcc, 'rdate': rdate, 'type_payment': 'card', 'bank_payment_id': id, 'user_id': user_id, 'source': 'mono',
        'account': account, 'mono_user_id': mono_user.id, 'is_deleted': is_deleted, "category_name": category_name,
        "balance": balance, 'currency': currency, "currency_amount": -1 * amount,
        # New currency tracking fields with proper values
        'amount_original': -1 * original_amount,
        'currency_original': original_currency,
        'exchange_rate': exchange_rate
    }

    return data_


def get_mono_payments(start_date: str = "", end_date: str = "", mono_user_id: int = None):

    result = []

    mono_user_info = get_mono_user_info__(mono_user_id)
    mono_user_token = mono_user_info['mono_user_token']
    accounts = mono_user_info.get('accounts')

    start_date_unix, end_date_unix = convert_dates(start_date, end_date)
    config_accounts = get_config_accounts(mono_user_id)

    for account in accounts:
        if account.get('balance') < 1:
            continue
        if account['id'] not in config_accounts:
            continue
        # If no accounts configured, process all active accounts
        # if config_accounts and account['id'] not in config_accounts:
        #     continue

        url = (f"{MONO_API_URL}/personal/statement/"
               f"{account['id']}/{start_date_unix}/{end_date_unix}")
        header = {"X-Token": mono_user_token}

        r = requests.get(url, headers=header)

        err_cnn = 0
        while r.status_code != 200:
            err_cnn += 1
            time_to_sleep = 15 + random.randint(10, 40)
            mono_logger.warning(
                f"""Status request code: {r.status_code}\nWait {time_to_sleep}s..."""
            )
            time.sleep(time_to_sleep)
            r = requests.get(url, headers=header)
            if err_cnn > 2:
                mono_logger.error("Error connection more then 2")
                return result

        result.extend(r.json())

    if len(result) < 1:
        mono_logger.info("No rows returned from Request..")

    return result


def process_mono_payments(
        user_id: int, start_date: str = None, end_date: str = None, mono_user_id: str = None, mode: str = None
):

    result = []
    result_html = 'Data not found'
    total_in = 0
    total_out = 0
    if not mono_user_id:
        mono_users = get_mono_users_(user_id)
    else:
        mono_users = [{"id": mono_user_id}]
    for mono_user_ in mono_users:
        mono_payments = get_mono_payments(start_date, end_date, mono_user_['id'])
        if not mono_payments:
            continue
        mono_user = db.session.query(MonoUser).get(mono_user_['id'])
        sql_result_th = ''
        if mode != 'show':
            sql_result_th = '<th>Sql</th>'
        result.append(
            f"""<b>{mono_user.name}</b>
<table class="table table-bordered"><tr><th>Дата</th><th>Опис</th><th>Розділ</th><th>Сума</th>{sql_result_th}</tr>"""
        )

        for mono_payment in mono_payments:
            data = convert_imp_mono_to_payment(user_id, mono_user, mono_payment)
            if not data:
                continue
            sql_result = None
            if mode == "import":
                sql_result = add_new_payment(data)
            elif mode == "sync":
                sql_result = sync_payment(data)
            sql_result_td = ''
            if mode != 'show':
                sql_result_td = f"""
                <td>{'<span style="color:green">✓</span>' if sql_result else '<span style="color:red">✗</span>'}</td>
                """
            result.append(
                f"""<tr><td>{data['rdate']} </td><td> {data['mydesc']}</td>
<td> {data['category_name']}</td><td> {-1 * data['amount']}</td>{sql_result_td}</tr>"""
            )
            if data['amount'] < 0:
                total_in -= data['amount']
            else:
                total_out += data['amount']

        result.append("</table>")
        result.append(f'Total in: {int(total_in)}, Total out: {int(total_out)}<br>')
        result_html = '\n'.join(result)

    return result_html


def get_user_id(account: str) -> int:
    user_id = 999999
    mono_account = db.session.query(Config).join(User).filter(
        Config.type_data == 'mono_account'
    ).filter(Config.value_data == account).one_or_none()

    if mono_account:
        user_id = mono_account.user_id
    return user_id


def get_mono_user(mono_user_id: int) -> MonoUser | None:
    mono_user = db.session.query(MonoUser).get(mono_user_id)

    if mono_user:
        return mono_user
    return None


def get_category_id(user_id: int, category_name: str) -> int:
    category = db.session.query(Category).filter(
        and_(
            Category.name.like(f'%{category_name}%'), Category.user_id == user_id, Category.parent_id == 0, )
    ).one_or_none()

    if category:
        category_id = category.id
    else:
        # new_category = Category()
        # data = {"name": category_name, "parent_id": 0, "user_id": user_id}
        # new_category.from_dict(**data)
        # db.session.add(new_category)
        # db.session.commit()
        # category_id = new_category.id
        category_id = 17  # Інші #TODO: need to do another something
    return category_id


def add_new_payment(data) -> Payment:
    result = None
    try:
        new_payment = Payment(**data)
        db.session.add(new_payment)
        db.session.commit()
        result = new_payment
    except Exception as err:
        db.session.rollback()
        db.session.flush()
        raise err
    return result


def sync_payment(data: dict) -> dict:
    result = None
    try:
        payment = db.session.query(Payment).filter(
            Payment.bank_payment_id == data['bank_payment_id']
        ).one_or_none()
        if payment:
            payment.update(**data)
        else:
            result = add_new_payment(data)
            return result
        db.session.commit()
        result = payment
    except Exception as err:
        db.session.rollback()
        db.session.flush()
        raise err
    return result


def get_mono_user_token(mono_user_id: int) -> str:
    mono_user = db.session.query(MonoUser).get(mono_user_id)
    return mono_user.token
