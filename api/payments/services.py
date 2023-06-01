import logging
import re
import datetime

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
    q = request.args.get("q")
    sort = request.args.get("sort")
    category_id = request.args.get("category_id")
    year = request.args.get("year")
    month = request.args.get("month")
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

    curr_date = datetime.datetime.now()
    if not year:
        year = f'{curr_date:%Y}'
    if not month:
        month = f'{curr_date:%m}'

    start_date = f'{year}-{int(month):02d}-01'
    end_date = f'{year if int(month) < 12 else int(year) + 1}-{int(month) + 1 if int(month) < 12 else 1:02d}-01'
    um.append(f" and p.`rdate` >= '{start_date}' and p.`rdate` < '{end_date}'")

    if mono_user_id:
        um.append(f" and p.`mono_user_id` = {mono_user_id}")

    if category_id:
        um.append(f" and (p.`category_id` = {category_id} or c.parent_id = {category_id})")
    else:
        um = []
        um.append(f" and p.rdate >= '{curr_date - datetime.timedelta(days=7):%Y-%m-%d}'")

    sql = f"""
select p.id, p.rdate, p.category_id, c.name as category_name
/*case 
    when c.parent_id = 0 then c.name
    else (select name from categories where id=c.parent_id)
end as category_name */
, c.parent_id, p.description, p.amount
from `payments` p left join categories c on p.category_id = c.id
where 1=1 and p.is_deleted = 0
{' '.join(um)}
{sort}
"""

    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    phone_number = ""
    result = do_sql_sel(sql)
    if not result:
        return []
    user_phones = get_user_phones_from_config(user_id)
    for row in result:
        if pattern.search(row["description"]):
            phone_number = pattern.search(row["description"]).group(0)
            phone_number = f'+38{phone_number}' if not phone_number.startswith('+38') else phone_number
            if phone_number in user_phones:
                row["description"] += f' [{user_phones[phone_number]}]'

    return result


def get_payment_(payment_id: int):
    """
    get info about payment
    """
    result = {}
    payment = db.session().query(Payment).get(payment_id)

    if not payment:
        abort(404, 'payment not found')

    result = payment.to_dict()
    result['category_name'] = payment.category.name

    refuel_data = {}
    if payment.category.name == 'Заправка':
        refuel_data = convert_desc_to_refuel_data(payment.description)
    if refuel_data:
        result['refuel_data'] = refuel_data

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
    update payment
    """
    data = request.get_json()
    if 'refuel_data' in data:
        data['description'] = conv_refuel_data_to_desc(data['refuel_data'])
    data["id"] = payment_id
    payment = db.session().query(Payment).get(payment_id)
    data['rdate'] = datetime.datetime.strptime(data['rdate'], '%Y-%m-%d')
    try:
        payment.from_dict(**data)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'payment edit failed {err}')
        abort(500, 'payment edit failed')

    # return payment.to_dict()
    return get_payment_(payment_id)
