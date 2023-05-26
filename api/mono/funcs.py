# _*_ coding:UTF-8 _*_
import logging
import time
import datetime
import random

import requests

from flask import current_app

from config import users, mono_api_url
from utils import do_sql_cmd

mono_logger = logging.getLogger('mono')
"""
url for webhook:
https://script.google.com/macros/s/AKfycbxq8R2y9ugmDmfYDAp9rf5MEUs_5lf2SNT_Cc0u_R3KYTfYMPvc/exec

https://api.monobank.ua/
POST /personal/webhook
{
  "webHookUrl": "string"
}
"""


def _mcc(mcc):
    if (
        mcc
        in (
            4011,
            4111,
            4112,
            4131,
            4304,
            4411,
            4415,
            4418,
            4457,
            4468,
            4511,
            4582,
            4722,
            4784,
            4789,
            5962,
            6513,
            7011,
            7032,
            7033,
            7512,
            7513,
            7519,
        )
        or mcc in range(3000, 4000)
    ):
        return "Подорожі"
    elif (
        mcc
        in (
            4119,
            5047,
            5122,
            5292,
            5295,
            5912,
            5975,
            5976,
            5977,
            7230,
            7297,
            7298,
            8011,
            8021,
            8031,
            8049,
            8050,
            8062,
            8071,
            8099,
        )
        or mcc in range(8041, 8044)
    ):
        return "Краса та медицина"
    elif (
        mcc
        in (
            5733,
            5735,
            5941,
            7221,
            7333,
            7395,
            7929,
            7932,
            7933,
            7941,
            7991,
            7995,
            8664,
        )
        or mcc in range(5970, 5974)
        or mcc in range(5945, 5948)
        or mcc in range(5815, 5819)
        or mcc in range(7911, 7923)
        or mcc in range(7991, 7995)
        or mcc in range(7996, 8000)
    ):
        return "Розваги та спорт"
    elif mcc in range(5811, 5815):
        return "Кафе та ресторани"
    elif mcc in (
        5297,
        5298,
        5300,
        5311,
        5331,
        5399,
        5411,
        5412,
        5422,
        5441,
        5451,
        5462,
        5499,
        5715,
        5921,
    ):
        return "Продукти й супермаркети"
    elif mcc in (7829, 7832, 7841):
        return "Кіно"
    elif (
        mcc
        in (
            5172,
            5511,
            5541,
            5542,
            5983,
            7511,
            7523,
            7531,
            7534,
            7535,
            7538,
            7542,
            7549,
        )
        or mcc in range(5531, 5534)
    ):
        return "Авто та АЗС"
    elif mcc in (
        5131,
        5137,
        5139,
        5611,
        5621,
        5631,
        5641,
        5651,
        5655,
        5661,
        5681,
        5691,
        5697,
        5698,
        5699,
        5931,
        5948,
        5949,
        7251,
        7296,
    ):
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
    if not start_date:
        start_date = datetime.datetime.today().strftime("%d.%m.%Y") + " 00:00:01"
    elif len(start_date) < 11:
        start_date += " 00:00:01"

    if not end_date:
        end_date = datetime.datetime.today().strftime("%d.%m.%Y") + " 23:59:59"
    elif len(end_date) < 11:
        end_date += " 23:59:59"

    start_date_unix = int(
        time.mktime(
            datetime.datetime.strptime(
                start_date, "%d.%m.%Y %H:%M:%S"
            ).timetuple()
        )
    )
    end_date_unix = int(
        time.mktime(
            datetime.datetime.strptime(
                end_date, "%d.%m.%Y %H:%M:%S"
            ).timetuple()
        )
    )
    return start_date_unix, end_date_unix    


def get_mono_pmts(start_date: str = "", end_date: str = "", user: str = "vik"):

    result = []
    token = None
    accounts = []

    for user_ in users:
        if user_.get('name') == user:
            token = user_.get("token")
            accounts = user_.get("account")
    
    if not any([token, accounts]):
        current_app.logger.error('Not find mono token')
        return result

    start_date_unix, end_date_unix = convert_dates(start_date, end_date)

    for account in accounts:
        url = f"""{mono_api_url}/personal/statement/{account}/{start_date_unix}/{end_date_unix}"""
        header = {"X-Token": token}

        r = requests.get(url, headers=header)

        err_cnn = 0
        while r.status_code != 200:
            err_cnn += 1
            Time2Sleep = 10 + random.randint(10, 30)
            current_app.logger.warning(
                f"""Status request code: {r.status_code}
                <br>Wait {Time2Sleep}s..."""
            )
            time.sleep(Time2Sleep)
            r = requests.get(url, headers=header)
            if err_cnn > 2:
                current_app.logger.error("Error connection more then 2")
                return result

        result.extend(r.json())
    
    if len(result) < 1:
        current_app.logger.info("No rows returned from Request..")

    return result


def process_mono_data_pmts(
        start_date: str = None,
        end_date: str = None,
        user: str = "vik",
        mode: str = None
    ):

    result = []
    result_html = 'Data not found'
    total_in = 0
    total_out = 0

    mono_pmts = get_mono_pmts(start_date, end_date, user)
    if not mono_pmts:
        return result_html
    
    result.append(
            """
<table class="table table-bordered"><tr><th>Дата</th><th>Опис</th><th>Розділ</th><th>Сума</th></tr>"""
        )

    for item in mono_pmts:
        data = {}
        data['end_date_'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item["time"]))
        data['id'] = item["id"]
        data['desc'] = item["description"]
        data['mcc'] = item["mcc"]
        data['cat'] = _mcc(item.get('mcc'))
        data['suma'] = -1 * item["amount"] / 100
        data['val'] = item["currencyCode"]
        data['bal'] = item["balance"]
        data['user'] = user

        if item["amount"] > 0:
            total_in += item["amount"]
        elif item["amount"] < 0:
            total_out += item["amount"]

        data['descnew'] = data['desc'].replace("\n", " ")
        mono_logger.info(f"{data}")

        if mode == "import":
            data['descnew'] = data['descnew'].replace("'", "")
            sql = """INSERT INTO `myBudj`  
(`rdate`, `id_bank`, `sub_cat`, `cat`, `mcc`, `suma`, `type_payment`, `source`, `owner`) 
VALUES 
(:end_date_, :id, :descnew, :cat, :mcc, :suma, 'CARD', 'mono', :user)"""
            do_sql_cmd(sql, data)
    
        result.append(
            f"""<tr><td>{data['end_date_']} </td><td> {data['descnew']}</td><td> {data['cat']}</td><td> {data['suma']}</td></tr>"""
        )

    result.append("</table>")
    result.append(f'total in: {int(total_in / 100)}, totsl out: {int(total_out / 100)}')
    result_html = '\n'.join(result)

    return result_html
