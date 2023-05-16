import re
from flask import current_app
from mydb import db, text
from datetime import datetime


def do_sql_cmd(sql="", data=None):
    try:
        conn = db.engine.connect()
    except Exception as e:
        current_app.logger.error(f"{sql}\n{e}")
        return {"rowcount": -1, "data": f"{e}"}        
    if data is None:
        data = {}
    sql = sql.strip()
    if re.search(r"^insert|^update|^delete|^commit", sql, re.I):
        try:
            res = conn.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": f"cnt: {res.rowcount}"}
        except Exception as e:
            current_app.logger.error(f"{sql}\n{e}")
            return {"rowcount": -1, "data": f"{e}"}
    elif re.search(r"^select|^with", sql, re.I):
        try:
            res = conn.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": res.fetchall()}
        except Exception as e:
            current_app.logger.error(f"{sql}\n{e}")
            return {"rowcount": -1, "data": f"""{e}\n{sql} """}
    else:
        current_app.logger.error(f"Неправильний запит\n{sql}")
        return {"rowcount": -1, "data": "Неправильний запит"}


def curr_date():
    return datetime.now().strftime("%d.%m.%Y")


def curr_datetime():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


# function for execute sql cmd
def do_sql(sql="", data=None):
    try:
        conn = db.engine.connect()
        if data is None:
            data = {}
        result = conn.execute(text(sql), data)
        cnt = result.rowcount
        return {"result": "ok", "msg": cnt}
    except Exception as e:
        current_app.logger.error(f"{sql}\n{e}")
        return {"result": "error", "msg": f"""error exec sql:\n{e}"""}


def do_sql_sel(sql="", data=None):
    try:
        conn = db.engine.connect()
        if data is None:
            data = {}
        return [r._asdict() for r in conn.execute(text(sql), data).fetchall()]
    except Exception as db_ee:
        current_app.logger.error(f"{sql}\n{db_ee}")
        return [{"rowcount": -1, "data": f"{db_ee}"}]
