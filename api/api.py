import datetime

from flask import Blueprint, request, jsonify, current_app, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin

from api.funcs import get_main_sql
from api.payments.funcs import get_dates
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

    current_date, end_date, start_date = get_dates(month, year)

    data = {
        "start_date": start_date,
        "end_date": end_date,
        "user_id": current_user.get('user_id'),
        "mono_user_id": request.args.get("mono_user_id"),
        "currency": request.args.get('currency', 'UAH') or 'UAH',
    }

    main_sql = get_main_sql(data)

    dialect_name = db.engine.dialect.name

    if dialect_name == 'sqlite':
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        amount_func = 'convert(sum(`amount`), UNSIGNED)'
    else:
        abort(400, f"Substring function not implemented for dialect: {dialect_name}")

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
{main_sql}
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
    dialect_name = db.engine.dialect.name

    if dialect_name == 'sqlite':
        substring_func = "strftime('%Y', `rdate`)"
        amount_func = "CAST(sum(`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        substring_func = 'extract(YEAR from `rdate`)'
        amount_func = 'convert(sum(`amount`), UNSIGNED)'
    else:
        abort(400, f"Substring function not implemented for dialect: {dialect_name}")

    current_user = get_jwt_identity()
    data = {"user_id": current_user.get('user_id')}
    if request.args.get("grouped"):
        main_sql = ("select rdate from `payments` "
                    "where amount > 0 and is_deleted = 0 and user_id = :user_id")
        add_fields = ""
    else:
        data["user_id"] = current_user.get('user_id')
        data["mono_user_id"] = request.args.get("mono_user_id")
        data["currency"] = request.args.get('currency', 'UAH') or 'UAH'
        add_fields = f", {amount_func} as amount, count(*) as cnt"

        main_sql = get_main_sql(data)

    sql = f"""
select {substring_func} as year {add_fields}
from 
(
{main_sql}
) p
where 1=1
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
    data = {
        "user_id": current_user.get('user_id'),
        "year": str(year),
        "mono_user_id": request.args.get("mono_user_id"),
        "currency": request.args.get('currency', 'UAH') or 'UAH',
    }
    main_sql = get_main_sql(data)

    dialect_name = db.engine.dialect.name
    if dialect_name == 'sqlite':
        month_func = "strftime('%m', p.`rdate`)"
        year_func = "strftime('%Y', p.`rdate`)"
        amount_func = "CAST(sum(p.`amount`) AS INTEGER)"
    elif dialect_name == 'mysql':
        month_func = 'extract(MONTH from p.`rdate`)'
        year_func = 'extract(YEAR from p.`rdate`)'
        amount_func = 'convert(sum(p.`amount`), UNSIGNED)'
    else:
        abort(400, f"Substring function not implemented for dialect: {dialect_name}")

    sql = f"""select 
{month_func} month, {amount_func} as amount,
count(*) as cnt
from 
(
{main_sql}
and {year_func} = :year
) p
where 1=1
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
