from flask import Blueprint, request, jsonify, current_app, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from mydb import db
from models.models import Category
from utils import do_sql_sel


api_bp = Blueprint(
    "api_bp",
    __name__,
    template_folder="templates/rozhody",
    static_folder="static",
)

@api_bp.route("/api/categories/", methods=["GET"])
@cross_origin()
@jwt_required()
def get_categories():
    """
    return  categories
    """
    current_user = get_jwt_identity()
    categories = db.session().query(Category).filter_by(
        user_id=current_user.get('id')
    ).all()
    try:
        return [category.to_dict() for category in categories]
    except Exception as err:
        current_app.logger.error(f"{err}")
        abort(500, f"{err}")



@api_bp.route("/api/payments/period", methods=["GET"])
@cross_origin()
@jwt_required()
def catcosts():
    """
    return payments grouped by categories in some period (year, month)
    """
    current_user = get_jwt_identity()
    year = request.args.get("year", "").zfill(2)
    month = request.args.get("month", "").zfill(2)
    mono_user_id = request.args.get("mono_user_id")
    period = f"""{year}{month}"""

    um_period = ""
    if not period or period == "0000":
        um_period = " and extract(YEAR_MONTH from rdate) = extract(YEAR_MONTH from now())"
    else:
        um_period = " and extract(YEAR_MONTH from rdate) = :period"
    
    um_user = ''
    if mono_user_id:
        um_user = " and mono_user_id = :mono_user_id"

    data = {"period": period, "mono_user_id": mono_user_id, "user_id": current_user.get('id')}

    sql = f"""
select p.category_id, c.name,convert(sum(`amount`),UNSIGNED) as amount,
count(*) as cnt
from `payments` p left join `categories` c
on p.categoy_id = c.id
where 1=1 
and p.user_id = :user_id
{um_period} {um_user} 
and `is_deleted` = 0
and `amount` > 0
group by p.category_id, c.name order by 2 desc
"""
    return do_sql_sel(sql, data)


@api_bp.route("/api/paymetns/years", methods=["GET"])
@cross_origin()
@jwt_required()
def years():
    """
    return total payments grouped by years
    """
    current_user = get_jwt_identity()
    mono_user_id = request.args.get("mono_user_id")
    um_mono_user = ''
    if mono_user_id:
        um_mono_user = " and mono_user_id = :mono_user_id"
    data = {"mono_user_id": mono_user_id, "user_id": current_user.get('id')}
    sql = f"""
select extract(YEAR from rdate) year,convert(sum(amount),UNSIGNED) as amount,count(*) as cnt
from `payments`
where 1=1
and `user_id` = :user_id
and `is_deleted` = 0
and `amount` > 0
{um_mono_user}
group by extract(YEAR from rdate) order by 1 desc
"""

    return jsonify([dict(row) for row in do_sql_sel(sql, data)])


@api_bp.route("/api/payments/years/<int:year>", methods=["GET"])
@cross_origin()
@jwt_required()
def months(year):
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
        "user_id": current_user.get('id'),
        "year": year
    }
    
    sql = f"""
select 
extract(MONTH from rdate) month,convert(sum(amount),UNSIGNED) as amount,
count(*) as cnt
from `payments`
where 1=1 and extract(YEAR from rdate) = :year
{um_mono_user}
group by extract(MONTH from rdate) order by 1 desc
"""

    return jsonify([dict(row) for row in do_sql_sel(sql, data)])


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
