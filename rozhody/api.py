import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_cors import cross_origin
from utils import do_sql_cmd, do_sql_sel

api_bp = Blueprint(
    "api_bp",
    __name__,
    template_folder="templates/rozhody",
    static_folder="static",
)

um_not_my_expspense = """
and sub_cat not in ('AliExpress','PAYPAL','PSP*mall.my.com','PAYPAL *GEEKBUYING','LIQPAY*Hosting Ukrayin','Pandao','Укрпошта','Нова пошта','portmone.com.ua','monobank','DHGATE','DHGATE.COM','wondershare')
and cat!='Грошові перекази' and `deleted`!=1
and suma>0
"""
cat4zam = """
if(sub_cat='Vdaliy Rik','Авто та АЗС',cat) as cat
"""

dict_phones = {
    "+380638457475": "Vik Life",
    "0500326725": "Vik Vodafone",
    "+380638508875": "Tanya Life",
    "0507558679": "Tanya Vodafone",
    "+380637054293": "Yarema Life",
    "+380633859083": "Yana Life",
    "+380634649973": "Ulya Life",
    "0684276934": "Ulya KS",
    "+380935420056": "Tato Life",
    "+380634650087": "Mama Life new",
    "+3809300281494": "Ulya Life 2",
    "0993954299": "Tato Vodafone",
    "+380639920388": "домашня Nokia",
}


@api_bp.route("/api/cats/", methods=["GET"])
@cross_origin()
def spr_cat():
    try:
        res = do_sql_cmd(
            f"""select distinct a.id,a.cat as name
from myBudj_spr_cat a
/*left join 
myBudj_sub_cat b 
on a.id=b.id_cat */
where a.ord!=0
order by a.ord""",
            False,
        )
        if len(res) < 1:
            return [{"id": "-1", "name": "result sql<1"}]
    except Exception as e:
        # myLog(f"{e}")
        return [{"id": "-1", "name": "error execute sql. check api.log for detail"}]
    return jsonify(res["data"])


@api_bp.route("/api/subcats/", methods=["GET"])
@cross_origin()
def do_sub_cat():
    cat = request.args.get("cat", "")
    um_cat = ""
    # #print(f"cat: {cat}")
    if cat:
        um_cat = (
            f""" and id_cat in (select id from `myBudj_spr_cat` where cat='{cat}')"""
        )
    sql = f"""select id,sub_cat as name 
from myBudj_sub_cat 
where 1=1 {um_cat}
order by ord"""
    # #print(f"{sql}")
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/catcosts", methods=["GET"])
@cross_origin()
@jwt_required()
def catcosts():
    year = request.args.get("year", "").zfill(2)
    month = request.args.get("month", "").zfill(2)
    period = f"""{year}{month}"""
    # #print(f"period: {period}")
    um_period = ""
    if not period or period == "0000":
        um_period = "extract(YEAR_MONTH from now())"
    else:
        um_period = f"{period}"
    sql = f"""
select {cat4zam},convert(sum(suma),UNSIGNED) as suma,count(*) as cnt
from `myBudj`
where extract(YEAR_MONTH from rdate)={um_period}
{um_not_my_expspense}
group by {cat4zam.replace(' as cat','')} order by 2 desc
"""
    # print(sql)
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/years", methods=["GET"])
@cross_origin()
@jwt_required()
def years():
    sql = f"""
select extract(YEAR from rdate) year,convert(sum(suma),UNSIGNED) as suma,count(*) as cnt
from `myBudj`
where 1=1
{um_not_my_expspense}
group by extract(YEAR from rdate) order by 1 desc
"""
    # print(sql)
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/months/<int:year>", methods=["GET"])
@cross_origin()
@jwt_required()
def months(year):
    # print(f"year: {year}")
    sql = f"""
select extract(MONTH from rdate) month,convert(sum(suma),UNSIGNED) as suma,count(*) as cnt
from `myBudj`
where 1=1 and extract(YEAR from rdate)={year}
{um_not_my_expspense}
group by extract(MONTH from rdate) order by 1 desc
"""
    # print(sql)
    return jsonify([dict(row) for row in do_sql_sel(sql)])


@api_bp.route("/api/costs", methods=["POST"])
@cross_origin()
@jwt_required()
def new_cost():
    req = request.get_json()
    res = do_sql_cmd(
        f"""insert into `myBudj` (rdate,cat,sub_cat,mydesc,suma) 
        values ('{req.get("rdate","")}', '{req['cat']}', '{req.get("sub_cat","")}','{req.get("mydesc","")}',{req['suma']})"""
    )
    if res["rowcount"] < 1:
        return jsonify({"status": "error", "data": res["data"]})

    return jsonify({"status": "ok", "data": res["data"], "id": res["rowcount"]})


@api_bp.route("/api/costs/", methods=["GET"])
# @cross_origin(supports_credentials=True)
@cross_origin()
@jwt_required()
def ret_costs():
    q = request.args.get("q", "")
    sort = request.args.get("sort", "")
    cat = request.args.get("cat", "")
    year = request.args.get("year", "")
    month = request.args.get("month", "")
    # print(f"sort: {sort}, year: {year}, month: {month}")

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
        um.append(f" and extract(YEAR from rdate)=extract(YEAR from now())")
    if month:
        um.append(f" and extract(MONTH from rdate)={month}")
    else:
        um.append(f" and extract(MONTH from rdate)=extract(MONTH from now())")

    if cat:
        um.append(f" and cat='{cat}'")

    sql = f"""
select id,rdate,cat,sub_cat,mydesc,suma
from `myBudj`
where 1=1 {' '.join(um)}
{um_not_my_expspense}
{sort}
"""
    # print(sql)
    pattern = re.compile(r"(\+38)?0\d{9}", re.MULTILINE)
    phone_number = ""
    res = [dict(row) for row in do_sql_sel(sql)]
    for r in res:
        if pattern.search(r["sub_cat"]):
            phone_number = pattern.search(r["sub_cat"]).group(0)
            if phone_number in dict_phones:
                r["mydesc"] += dict_phones[phone_number]

    return jsonify(res)


@api_bp.route("/api/costs/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def ret_cost(id):
    sql = f"select id,rdate,cat,sub_cat,mydesc,suma from myBudj where id={id}"
    res = do_sql_sel(sql)
    # for r in res:
    # print(f"{r=}")
    # return jsonify([dict(row) for row in do_sql_sel(sql)])
    return jsonify([dict(row) for row in res])


@api_bp.route("/api/costs/<int:id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def del_cost(id):
    res = do_sql_cmd(f"update myBudj set deleted=1 where id={id}")
    if res["rowcount"] < 1:
        return jsonify({"status": "error", "data": res["data"]})

    return jsonify({"status": "ok", "data": res["data"]})


@api_bp.route("/api/costs/<id>", methods=["PUT"])
@cross_origin()
@jwt_required()
def upd_cost(id):
    req = request.get_json()
    sql = f"""update myBudj set cat='{req['cat']}', rdate='{req['rdate']}', sub_cat='{req.get("sub_cat","")}',mydesc='{req.get("mydesc","")}'
        ,suma={req['suma']}  
        where id={id}"""
    # print(sql)
    res = do_sql_cmd(sql)
    if res["rowcount"] < 1:
        return jsonify({"status": "error", "data": res["data"]})

    return jsonify({"status": "ok", "data": res["data"]})


@api_bp.route("/api/about", methods=["GET"])
@cross_origin()
def about():
    try:
        with open("app/rozhody/txt/about.html", encoding="utf8") as f:
            data = f.read()
    except:
        return jsonify({"status": "error", "data": "error open about file"})

    return jsonify({"status": "ok", "data": data})
