import re
from mydb import db, text
from datetime import datetime


def do_sql_cmd(sql="", data=None):
    conn = db.engine.connect()
    if data is None:
        data = {}
    sql = sql.strip()
    if re.search(r"^insert|^update|^delete|^commit", sql, re.I):
        try:
            res = conn.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": f"cnt: {res.rowcount}"}
        except Exception as e:
            with open("fin_man_debugger.log", "a", encoding="utf8") as f:
                f.write(f"{sql}\n{e}")
            return {"rowcount": -1, "data": f"{e}"}
    elif re.search(r"^select|^with", sql, re.I):
        try:
            res = conn.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": res.fetchall()}
        except Exception as e:
            with open("fin_man_debugger.log", "a", encoding="utf8") as f:
                f.write(f"{sql}\n{e}")
            return {"rowcount": -1, "data": f"""{e}\n{sql} """}
    else:
        return {"rowcount": -1, "data": "Неправильний запит"}


def curr_date():
    return datetime.now().strftime("%d.%m.%Y")


def curr_datetime():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


# function for execute sql cmd
def do_sql(sql="", data=None):
    conn = db.engine.connect()
    if data is None:
        data = {}
    try:
        result = conn.execute(text(sql), data)
        cnt = result.rowcount
        return {"result": "ok", "msg": cnt}
    except Exception as e:
        return {"result": "error", "msg": f"""error exec sql:\n{e}"""}


def do_sql_sel(sql="", data=None):
    conn = db.engine.connect()
    if data is None:
        data = {}
    try:
        return [r._asdict() for r in conn.execute(text(sql), data).fetchall()]
    except Exception as db_ee:
        with open("fin_man_debugger.log", "a", encoding="utf8") as f:
            f.write(f"{sql}\n{db_ee}")
        return [{"rowcount": -1, "data": f"{db_ee}"}]
