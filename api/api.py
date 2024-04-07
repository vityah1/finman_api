import datetime

from flask import Blueprint, request, jsonify, current_app, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin

from api.funcs import get_last_rate
from mydb import db
from utils import do_sql_sel


api_bp = Blueprint(
    "api_bp",
    __name__,
    template_folder="templates/rozhody",
    static_folder="static",
)


@api_bp.route("/api/payments/period", methods=["GET"])
@cross_origin()
@jwt_required()
def payments_for_period():
    """
    return payments grouped by categories in some period (year, month)
    """
    current_user = get_jwt_identity()
    year = request.args.get("year", "").zfill(2)
    month = request.args.get("month", "").zfill(2)
    mono_user_id = request.args.get("mono_user_id")
    currency = request.args.get('currency', 'UAH') or 'UAH'

    condition = []
    curr_date = datetime.datetime.now()
    if not year:
        year = f'{curr_date:%Y}'
    if not month:
        month = f'{curr_date:%m}'

    start_date = f'{year}-{int(month):02d}-01'
    end_date = f'{year if int(month) < 12 else int(year) + 1}-{int(month) + 1 if int(month) < 12 else 1:02d}-01'
    condition.append(" and p.`rdate` >= :start_date and p.`rdate` < :end_date")

    if mono_user_id:
        condition.append(" and mono_user_id = :mono_user_id")

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "mono_user_id": mono_user_id,
        "user_id": current_user.get('user_id')
    }

    dialect_name = db.engine.dialect.name

    if dialect_name == 'sqlite':
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        amount_func = 'convert(sum(`amount`), UNSIGNED)'
    else:
        abort(400, f"Substring function not implemented for dialect: {dialect_name}")

    saleRate = get_last_rate(currency, end_date)

    sql = f"""
select 
case 
    when c.parent_id = 0 then p.category_id
    else (select id from categories where id=c.parent_id)
end as category_id
, 
case 
    when c.parent_id = 0 then c.name
    else (select name from categories where id=c.parent_id)
end as name
, {amount_func} as amount,
count(*) as cnt
from (
SELECT p.id, p.rdate, p.category_id, p.mydesc,
       CASE
           WHEN p.currency = '{currency}' THEN p.currency_amount
           WHEN p.currency = 'UAH' AND '{currency}' IN ('EUR', 'USD') and e.saleRate is not null THEN p.currency_amount / e.saleRate
           WHEN p.currency IN ('EUR', 'USD') AND '{currency}' = 'UAH' and e.saleRate is not null THEN p.currency_amount * e.saleRate
           WHEN p.currency = 'UAH' AND '{currency}' IN ('EUR', 'USD') and e.saleRate is null THEN p.currency_amount / {saleRate}
           WHEN p.currency IN ('EUR', 'USD') AND '{currency}' = 'UAH' and e.saleRate is null THEN p.currency_amount *
{saleRate}
           ELSE p.currency_amount
       END AS amount
FROM `payments` p
LEFT JOIN (
    SELECT e1.rdate, e1.currency, e1.saleRate, e1.purchaseRate
    FROM spr_exchange_rates e1
    JOIN (
        SELECT DATE(rdate) AS date, MAX(rdate) AS max_rdate
        FROM spr_exchange_rates
        WHERE currency = '{currency}'
        GROUP BY DATE(rdate)
    ) e2 ON DATE(e1.rdate) = e2.date AND e1.rdate = e2.max_rdate
    WHERE e1.currency = '{currency}'
) e ON DATE(e.rdate) = DATE(p.rdate)
where 1=1
and p.user_id = :user_id
and `is_deleted` = 0
and `amount` > 0
{' '.join(condition)}
) p left join `categories` c
on p.category_id = c.id
where 1=1 
group by case 
    when c.parent_id = 0 then p.category_id
    else (select id from categories where id=c.parent_id)
end
, 
case 
    when c.parent_id = 0 then c.name
    else (select name from categories where id=c.parent_id)
end order by 3 desc
"""
    return do_sql_sel(sql, data)


@api_bp.route("/api/payments/years", methods=["GET"])
@cross_origin()
@jwt_required()
def payments_by_years():
    """
    return total payments grouped by years
    """
    current_user = get_jwt_identity()
    mono_user_id = request.args.get("mono_user_id")
    um_mono_user = ''
    if mono_user_id:
        um_mono_user = " and mono_user_id = :mono_user_id"
    data = {"mono_user_id": mono_user_id, "user_id": current_user.get('user_id')}

    dialect_name = db.engine.dialect.name

    if dialect_name == 'sqlite':
        substring_func = "strftime('%Y', `rdate`)"
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        substring_func = 'extract(YEAR from `rdate`)'
        amount_func = 'convert(sum(`amount`), UNSIGNED)'
    else:
        abort(400, f"Substring function not implemented for dialect: {dialect_name}")

    sql = f"""
select {substring_func} as year, {amount_func} as amount, count(*) as cnt
from `payments`
where 1=1
and `user_id` = :user_id
and `is_deleted` = 0
and `amount` > 0
{um_mono_user}
group by {substring_func} order by 1 desc
"""

    return do_sql_sel(sql, data)


@api_bp.route("/api/payments/years/<int:year>", methods=["GET"])
@cross_origin()
@jwt_required()
def payment_by_months(year):
    """
    return total payments grouped by months in year
    """
    current_user = get_jwt_identity()
    mono_user_id = request.args.get("mono_user_id")
    um_mono_user = ''
    if mono_user_id:
        um_mono_user = " and mono_user_id = :mono_user_id"
    data = {
        "mono_user_id": mono_user_id,
        "user_id": current_user.get('user_id'),
        "year": str(year)
    }

    dialect_name = db.engine.dialect.name
    if dialect_name == 'sqlite':
        month_func = "strftime('%m', `rdate`)"
        year_func = "strftime('%Y', `rdate`)"
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        month_func = 'extract(MONTH from `rdate`)'
        year_func = 'extract(YEAR from `rdate`)'
        amount_func = 'convert(sum(`amount`), UNSIGNED)'
    else:
        abort(400, f"Substring function not implemented for dialect: {dialect_name}")

    sql = f"""select 
{month_func} month, {amount_func} as amount,
count(*) as cnt
from `payments`
where 1=1 and `user_id` = :user_id and {year_func} = :year
{um_mono_user}
group by {month_func} order by 1 desc
"""

    return do_sql_sel(sql, data)


@api_bp.route("/api/about", methods=["GET"])
@cross_origin()
def about():
    """
    return content of /txt/about.html
    """
    try:
        with open("txt/about.html", encoding="utf8") as f:
            data = f.read()
    except Exception as err:
        current_app.logger.error(f"{err}")
        return jsonify({"status": "error", "data": "error open about file"})

    return jsonify({"status": "ok", "data": data})
