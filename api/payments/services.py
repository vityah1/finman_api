import datetime
import logging
import re

from flask import abort, jsonify, request

from api.funcs import get_last_rate, get_main_sql
from api.payments.funcs import (
    conv_refuel_data_to_desc, convert_desc_to_refuel_data, create_bank_payment_id, get_user_phones_from_config,
)
from models import Payment
from mydb import db
from utils import do_sql_sel

logger = logging.getLogger()


def add_payment_(user_id: int):
    """
    insert a new payment
    """
    data = request.get_json()
    data['user_id'] = user_id
    if "refuel_data" in data and "km" in data["refuel_data"] and data["refuel_data"]["km"]:
        result = conv_refuel_data_to_desc(data["refuel_data"])
        if result:
            data['mydesc'] = result
    data['bank_payment_id'] = create_bank_payment_id(data)
    if data['currency'] != 'UAH':
        data['amount'] = float(data['currency_amount']) * get_last_rate(data['currency'], data['rdate'])
    payment = Payment()
    payment.from_dict(**data)
    try:
        db.session().add(payment)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"payment add failed {err}")
        abort(500, "payment add failed")

    return payment.to_dict()


def get_payments_detail(user_id: int) -> list[dict]:
    """
    list or search all payments.
    if not set conditions year and month then get current year and month
    if set q then do search
    """

    sort = request.args.get("sort")
    category_id = request.args.get("category_id")
    year = request.args.get("year")
    month = request.args.get("month")
    currency = request.args.get('currency', 'UAH') or 'UAH'

    um = []

    if not sort:
        sort = "order by `amount` desc"
    elif sort == "1":
        sort = "order by `rdate` desc"
    elif sort == "2":
        sort = "order by `category_id`"
    elif sort == "3":
        sort = "order by `amount` desc"
    else:
        sort = "order by `amount` desc"

    current_date = datetime.datetime.now()
    if not year:
        year = f"{current_date:%Y}"
    if not month:
        month = f"{current_date:%m}"

    start_date = f"{year}-{int(month):02d}-01"
    end_date = f"{year if int(month) < 12 else int(year) + 1}-{int(month) + 1 if int(month) < 12 else 1:02d}-01"

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "user_id": user_id,
        "mono_user_id": request.args.get("mono_user_id"),
        "currency": currency,
        "q": request.args.get("q")
    }

    main_sql = get_main_sql(data)

    if category_id:
        data["category_id"] = category_id
        um.append(f" and (p.`category_id` = :category_id or c.parent_id = :category_id)")
    else:
        um = []
        um.append(f" and p.rdate >= '{current_date - datetime.timedelta(days=7):%Y-%m-%d}'")

    sql = f"""
SELECT p.id, p.rdate, p.category_id, c.name AS category_name,
       c.parent_id, p.mydesc, p.amount,
       m.name AS mono_user_name, p.currency, p.currency_amount, p.saleRate
from ({main_sql}) p
LEFT JOIN categories c ON p.category_id = c.id
LEFT OUTER JOIN mono_users m on p.mono_user_id = m.id
WHERE 1=1
{' '.join(um)}
{sort}
"""

    result = do_sql_sel(sql, data)
    if not result:
        return []

    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    user_phones = get_user_phones_from_config(user_id)
    for row in result:

        if pattern.search(row["mydesc"]):
            phone_number = pattern.search(row["mydesc"]).group(0)
            phone_number = f"+38{phone_number}" if not phone_number.startswith("+38") else phone_number
            if phone_number in user_phones:
                row["mydesc"] += f" [{user_phones[phone_number]}]"
        #
        # if row["currency"] != currency:
        #     if row["currency"] == 'UAH':
        #         row["amount"] = round(row["currency_amount"] /
        #                               (row["saleRate"] if row.get("saleRate") else saleRate), 2)
        #     else:
        #         row["amount"] = round(row["currency_amount"] *
        #                               (row["saleRate"] if row.get("saleRate") else saleRate), 2)
        # else:
        #     row["amount"] = round(row["currency_amount"], 2)

    return result


def get_payment_(payment_id: int):
    """
    get info about payment
    """
    result = {}
    payment = db.session().query(Payment).get(payment_id)

    if not payment:
        abort(404, "payment not found")

    result = payment.to_dict()
    result["category_name"] = payment.category.name

    refuel_data = {}
    if payment.category.name == "Заправка":
        refuel_data = convert_desc_to_refuel_data(payment.mydesc)
    if refuel_data:
        result["refuel_data"] = refuel_data

    return result


def del_payment_(payment_id: int):
    """
    mark delete payment
    """
    payment = db.session().query(Payment).get(payment_id)
    payment.is_deleted = True
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"set payment as deleted failed {err}")
        abort(500, "set payment as deleted failed")

    return jsonify({"status": "ok"})


def upd_payment_(payment_id):
    """
    update payment
    """
    data = request.get_json()
    if "refuel_data" in data and "km" in data["refuel_data"] and data["refuel_data"]["km"]:
        data["mydesc"] = conv_refuel_data_to_desc(data["refuel_data"])
    data["id"] = payment_id
    payment = db.session().query(Payment).get(payment_id)
    data["rdate"] = datetime.datetime.strptime(data["rdate"], "%Y-%m-%d")
    try:
        payment.update(**data)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"payment edit failed {err}")
        abort(500, "payment edit failed")

    # return payment.to_dict()
    return get_payment_(payment_id)
