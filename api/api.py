from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_cors import cross_origin
from utils import do_sql_sel
from func import um_not_my_expspense, cat4zam

api_bp = Blueprint(
    "api_bp",
    __name__,
    template_folder="templates/rozhody",
    static_folder="static",
)


@api_bp.route("/api/cats/", methods=["GET"])
@cross_origin()
def spr_cat():
    """
    return list of catalogs
    """
    sql = f"""select distinct a.id,a.cat as name
from `myBudj_spr_cat` a
/*left join 
`myBudj_sub_cat` b 
on a.id=b.id_cat */
where a.ord!=0
order by a.ord"""

    try:
        return jsonify([dict(row) for row in do_sql_sel(sql)])
    except Exception as e:
        # myLog(f"{e}")
        return [{"id": "-1", "name": f"error {e}"}]


@api_bp.route("/api/subcats/", methods=["GET"])
@cross_origin()
def do_sub_cat():
    """
    return list of sub_catalogs
    """
    cat = request.args.get("cat", "")
    um_cat = ""
    # #print(f"cat: {cat}")
    if cat:
        um_cat = (
            f""" and id_cat in (select id from `myBudj_spr_cat` where cat='{cat}')"""
        )
    sql = f"""select id,sub_cat as name, id_cat 
from `myBudj_sub_cat` 
where 1=1 {um_cat}
order by ord"""
    # #print(f"{sql}")
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/catcosts", methods=["GET"])
@cross_origin()
@jwt_required()
def catcosts():
    """
    return costs grouped by cat in some period (year, month)
    """
    year = request.args.get("year", "").zfill(2)
    month = request.args.get("month", "").zfill(2)
    user = request.args.get("user", "all")
    period = f"""{year}{month}"""
    # #print(f"period: {period}")
    um_period = ""
    if not period or period == "0000":
        um_period = " and extract(YEAR_MONTH from rdate)=extract(YEAR_MONTH from now())"
    else:
        um_period = f" and extract(YEAR_MONTH from rdate)={period}"
    um_user = ''
    if user not in ('all', '', 'undefined'):
        um_user = f" and owner = '{user}'"
    sql = f"""
select {cat4zam},convert(sum(suma),UNSIGNED) as suma,count(*) as cnt
from `myBudj`
where 1=1 {um_period} {um_user} {um_not_my_expspense}
group by {cat4zam.replace(' as cat','')} order by 2 desc
"""
    return do_sql_sel(sql)


@api_bp.route("/api/years", methods=["GET"])
@cross_origin()
@jwt_required()
def years():
    """
    return total costs grouped by years
    """
    user = request.args.get("user", "all")
    um_user = ''
    if user not in ('all', '', 'undefined'):
        um_user = f" and owner = '{user}'"    
    sql = f"""
select extract(YEAR from rdate) year,convert(sum(suma),UNSIGNED) as suma,count(*) as cnt
from `myBudj`
where 1=1
{um_not_my_expspense} {um_user}
group by extract(YEAR from rdate) order by 1 desc
"""
    # print(sql)
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/months/<int:year>", methods=["GET"])
@cross_origin()
@jwt_required()
def months(year):
    """
    return total costs grouped by months in some year
    """
    user = request.args.get("user", "all")
    um_user = ''
    if user not in ('all', '', 'undefined'):
        um_user = f" and owner = '{user}'"     
    sql = f"""
select extract(MONTH from rdate) month,convert(sum(suma),UNSIGNED) as suma,count(*) as cnt
from `myBudj`
where 1=1 and extract(YEAR from rdate)={year}
{um_not_my_expspense} {um_user}
group by extract(MONTH from rdate) order by 1 desc
"""
    # print(sql)
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/about", methods=["GET"])
@cross_origin()
def about():
    """
    return content of /txt/about.html
    """
    try:
        with open("txt/about.html", encoding="utf8") as f:
            data = f.read()
    except:
        return jsonify({"status": "error", "data": "error open about file"})

    return jsonify({"status": "ok", "data": data})
