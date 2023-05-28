import logging
import re

from flask import request, jsonify, abort

from mydb import db
from models import Payment
from utils import do_sql_sel
from api.payments.funcs import (
    conv_refuel_data_to_desc,
    convert_desc_to_refuel_data,
    get_user_phones_from_config,
)


logger = logging.getLogger()


def add_payment_():
    """
    insert a new cost
    input: rdate,cat,sub_cat,mydesc,suma
    """
    data = request.get_json()
    if data.get('km') and data.get('litres'):
        result = conv_refuel_data_to_desc(data)
        if result:
            data = result
    payment = Payment()
    payment.from_dict(**data)
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'payment add failed {err}') 
        abort(500, 'payment add failed')

    return payment.to_dict()


def get_payments_(user_id: int) -> list[dict]:
    """
    list or search all payments.
    if not set conditions year and month then get current year and month
    if set q then do search
    """
    q = request.args.get("q", "")
    sort = request.args.get("sort", "")
    category_id = request.args.get("category_id")
    year = request.args.get("year", "")
    month = request.args.get("month", "")
    mono_user_id = request.args.get("mono_user_id")

    um = []

    if q:
        um.append(
            f" and (c.`name` like '%{q}%' or `descript` like '%{q}%')"
        )

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

    if year:
        um.append(f" and extract(YEAR from `rdate`) = {year}")
    else:
        um.append(" and extract(YEAR from `rdate`) = extract(YEAR from now())")
    if month:
        um.append(f" and extract(MONTH from `rdate`) = {month}")
    else:
        um.append(" and extract(MONTH from `rdate`) = extract(MONTH from now())")

    if mono_user_id:
        um.append(" and `mono_user_id` = '{}'".format(mono_user_id))

    if category_id:
        um.append(f" and `category_id` = {category_id}")
    else:
        um = []
        um.append(" and rdate >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY) ")

    sql = f"""
select p.id, p.rdate, p.category_id, c.name, descript, amount
from `payments` p left join categories c on p.category_id = c.id
where 1=1 {' '.join(um)}
{sort}
"""

    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    phone_number = ""
    res = [dict(row) for row in do_sql_sel(sql)]
    if res[0].get("rowcount") is not None and res[0].get("rowcount") < 0:
        return jsonify([{"cat": "Помилки", "mydesc": "Помилка виконання запиту"}])
    user_phones = get_user_phones_from_config(user_id)
    for r in res:
        if pattern.search(r["descript"]):
            phone_number = pattern.search(r["descript"]).group(0)
            if phone_number in user_phones:
                r["descript"] += user_phones[phone_number]

    return jsonify(res)


def get_payment_(payment_id: int):
    """
    get info about payment
    """
    result = {}
    payment = db.session().query(Payment).get(payment_id)
    
    if not payment:
        abort(404, 'payment not found')

    refuel_data = {}

    if payment.category.name == 'Заправка':
        refuel_data = convert_desc_to_refuel_data(payment.description)
    result = payment.to_dict()
    if refuel_data:
        result.update(refuel_data)

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
        logger.error(f'set payment as deleted failed {err}')
        abort(500, 'set payment as deleted failed')

    return jsonify({"status": "ok"})


def upd_payment_(payment_id):
    """
    update a cost
    input: rdate,cat,sub_cat,mydesc,suma,id
    """
    data = conv_refuel_data_to_desc(request.get_json())
    data["id"] = payment_id
    payment = db.session().query(Payment).get(payment_id)
    try:
        payment.from_dict(**data)
        db.session().commit
    except Exception as err:
        db.session().rollback()
        logger.error(f'payment edit failed {err}')
        abort(500, 'payment edit failed')

    return payment.to_dict()
