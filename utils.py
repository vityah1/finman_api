import re
from flask import current_app
from mydb import db, text
from datetime import datetime


def curr_date():
    return datetime.now().strftime("%d.%m.%Y")


def curr_datetime():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def do_sql_cmd(sql="", data=None):
    if data is None:
        data = {}
    try:
        sql = sql.strip()
        with db.session() as sess:
            conn = sess.connection()
            res = conn.execute(text(sql), data)
            if re.search(r"^insert|^update|^delete|^commit", sql, re.I):
                
                return {
                    "rowcount": res.rowcount,
                    "data": res.lastrowid if res.lastrowid else res.rowcount
                    }
            elif re.search(r"^select|^with", sql, re.I):
                return {"rowcount": res.rowcount, "data": res.fetchall()}
            else:
                current_app.logger.error(f"Неправильний запит\n{sql}")
                return {"rowcount": -1, "data": "Неправильний запит"}
    except Exception as db_err:
        current_app.logger.error(f"{sql}\n{db_err}")
        return {"rowcount": -1, "data": f"{db_err}"}


def do_sql(sql="", data=None):
    if data is None:
        data = {}
    try:
        with db.session() as sess:
            conn = sess.connection()
            result = conn.execute(text(sql), data)
            return {"result": "ok", "msg": result.rowcount}
    except Exception as db_err:
        current_app.logger.error(f"{sql}\n{db_err}")
        return {"result": "error", "msg": f"error exec sql:\n{db_err}"}


def do_sql_sel(sql="", data=None):
    if data is None:
        data = {}
    try:
        with db.session() as sess:
            conn = sess.connection()
            return [r._asdict() for r in conn.execute(text(sql), data).fetchall()]
    except Exception as db_err:
        current_app.logger.error(f"{sql}\n{db_err}")
        raise Exception("error exec sql:\n{}".format(db_err))
        # return [{"rowcount": -1, "data": f"{db_err}"}]


def convert_currency_code(code: int) -> str:
    conversion_map = {
        840: "USD",
        978: "EUR",
        980: "UAH"
    }
    return conversion_map.get(code, "UNKNOWN")