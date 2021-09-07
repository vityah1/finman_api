import re
from mydb import db, text
from datetime import datetime


def do_sql_cmd(sql="", data=None):
    if data is None:
        data = {}
    sql = sql.strip()
    if re.search(r"^insert|^update|^delete|^commit", sql, re.I):
        try:
            res = db.engine.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": f"cnt: {res.rowcount}"}
        except Exception as e:
            with open("fin_man_debugger.log", "a", encoding="utf8") as f:
                f.write(f"{sql}\n{e}")
            # print(f"""def do_sql_cmd: error exec sql:\n{e}\n{sql}""")
            return {"rowcount": -1, "data": f"{e}"}
    elif re.search(r"^select|^with", sql, re.I):
        try:
            res = db.engine.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": res.fetchall()}
        except Exception as e:
            with open("fin_man_debugger.log", "a", encoding="utf8") as f:
                f.write(f"{sql}\n{e}")
            # print(f"""def do_sql_cmd: error exec sql:\n{e}\n{sql}""")
            return {"rowcount": -1, "data": f"""{e}\n{sql} """}
    else:
        # print(f"""not valid sql\n{sql}""")
        return {"rowcount": -1, "data": "Неправильний запит"}


def curr_date():
    return datetime.now().strftime("%d.%m.%Y")


def curr_datetime():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


# function for execute sql cmd
def do_sql(sql="", data=None):
    if data is None:
        data = {}
    try:
        result = db.engine.execute(text(sql), data)
        cnt = result.rowcount
        return {"result": "ok", "msg": cnt}
    except Exception as e:
        return {"result": "error", "msg": f"""error exec sql:\n{e}"""}


def do_sql_sel(sql="", data=None):
    if data is None:
        data = {}
    try:
        return db.engine.execute(text(sql), data).fetchall()
        # return result
    except Exception as e:
        with open("fin_man_debugger.log", "a", encoding="utf8") as f:
            f.write(f"{sql}\n{e}")
        return [{"rowcount": -1, "data": f"{e}"}]