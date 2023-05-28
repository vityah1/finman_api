import re

from flask import request, jsonify

from utils import do_sql_sel
from func import cfg, um_not_my_expspense
from api.payments.payments_funcs import conv_refuel_data_to_desc
from mydb import db
from models import Payment


dict_phones = cfg.get("dict_phones")


def add_payment_():
    """
    insert a new cost
    input: rdate,cat,sub_cat,mydesc,suma
    """
    data = conv_refuel_data_to_desc(request.get_json())
    payment = Payment()
    payment.from_dict(data)
    try:
        db.session().commit()
    except Exception as err:
        return jsonify({"status": "error", "data": str(err)})

    return payment.to_dict()


def get_payments_():
    """
    list or search all costs.
    if not set conditions year and month then get current year and month
    if set q then do search
    input: q,cat,year,month
    """
    q = request.args.get("q", "")
    sort = request.args.get("sort", "")
    cat = request.args.get("cat", "")
    year = request.args.get("year", "")
    month = request.args.get("month", "")
    user = request.args.get("user", "all")

    um = []

    if q:
        um.append(
            f" and (`cat` like '%{q}%' or  `sub_cat` like '%{q}%' or  `mydesc` like '%{q}%' or `owner` like '%{q}%')"
        )

    if not sort:
        sort = "order by suma desc"
    elif sort == "1":
        sort = "order by rdate desc"
    elif sort == "2":
        sort = "order by cat"
    elif sort == "3":
        sort = "order by suma desc"
    else:
        sort = "order by  suma desc"

    if year:
        um.append(f" and extract(YEAR from rdate)={year}")
    else:
        um.append(" and extract(YEAR from rdate)=extract(YEAR from now())")
    if month:
        um.append(f" and extract(MONTH from rdate)={month}")
    else:
        um.append(" and extract(MONTH from rdate)=extract(MONTH from now())")

    if user and user != 'all':
        um.append(" and owner = '{}'".format(user))

    if cat and cat != "last":
        um.append(f" and cat='{cat}'")
    else:
        um = []
        um.append(" and rdate>=DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY) ")

    sql = f"""
select id,rdate,cat,sub_cat,mydesc,suma
from `myBudj`
where 1=1 {' '.join(um)}
{um_not_my_expspense}
{sort}
"""

    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    phone_number = ""
    res = [dict(row) for row in do_sql_sel(sql)]
    if res[0].get("rowcount") is not None and res[0].get("rowcount") < 0:
        return jsonify([{"cat": "Помилки", "mydesc": "Помилка виконання запиту"}])
    for r in res:
        if pattern.search(r["sub_cat"]):
            phone_number = pattern.search(r["sub_cat"]).group(0)
            if phone_number in dict_phones:
                r["mydesc"] += dict_phones[phone_number]

    return jsonify(res)


def get_payment_(payment_id: int):
    """
    get info about cost
    input: id
    """
    payment = db.session().query(Payment).get(payment_id)
    row = payment.to_dict()

    if row.get('sub_cat') == 'Заправка':
        try:
            row['km'] = re.search('(\d+)км;', row.get('mydesc')).groups(0)
        except:
            pass
        try:
            row['litres'] = re.search('(\d+)л;', row.get('mydesc')).groups(0)
        except:
            pass
        try:
            row['price_val'] = re.search('(\d+(\.)?(\d+)?)eur', row.get('mydesc')).group(1)
        except:
            pass            
        try:                
            row['name'] = row.get('mydesc').split(';')[-1]
        except:
            pass                

    return row


def del_payment_(payment_id: int):
    """
    mark delete cost
    input: id
    """
    payment = db.session().query(Payment).get(payment_id)
    payment.is_deleted = True
    try:
        db.session().commit()
    except Exception as err:
        return jsonify({"status": "error", "data": str(err)})

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
        payment.from_dict(data)
        db.session().commit
    except Exception as err:
        return jsonify({"status": "error", "data": str(err)})

    return payment.to_dict()
