import re
import logging
from mydb import text
from fastapi_sqlalchemy import db
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)


def curr_date():
    return datetime.now().strftime("%d.%m.%Y")


def curr_datetime():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def do_sql_cmd(sql="", data=None):
    """
    Виконати SQL запит та повернути результат
    """
    if data is None:
        data = {}
    try:
        sql = sql.strip()
        # Use db.session from fastapi_sqlalchemy context
        conn = db.session.connection()
        res = conn.execute(text(sql), data)
        if re.search(r"^insert|^update|^delete|^commit", sql, re.I):
            return {
                "rowcount": res.rowcount,
                "data": res.lastrowid if res.lastrowid else res.rowcount
            }
        elif re.search(r"^select|^with", sql, re.I):
            return {"rowcount": res.rowcount, "data": res.fetchall()}
        else:
            logger.error(f"Неправильний запит\n{sql}")
            return {"rowcount": -1, "data": "Неправильний запит"}
    except Exception as db_err:
        logger.error(f"{sql}\n{db_err}")
        return {"rowcount": -1, "data": f"{db_err}"}


def do_sql(sql="", data=None):
    """
    Виконати SQL запит та повернути результат у вигляді статусу
    """
    if data is None:
        data = {}
    try:
        conn = db.session.connection()
        result = conn.execute(text(sql), data)
        return {"result": "ok", "msg": result.rowcount}
    except Exception as db_err:
        logger.error(f"{sql}\n{db_err}")
        return {"result": "error", "msg": f"error exec sql:\n{db_err}"}


def do_sql_sel(sql="", data=None):
    """
    Виконати SQL запит та повернути список результатів
    """
    if data is None:
        data = {}
    try:
        conn = db.session.connection()
        return [r._asdict() for r in conn.execute(text(sql), data).fetchall()]
    except Exception as db_err:
        logger.error(f"{sql}\n{db_err}")
        raise Exception(f"error exec sql:\n{db_err}")


def convert_currency_code(code: int) -> str:
    conversion_map = {
        840: "USD",
        978: "EUR",
        980: "UAH"
    }
    return conversion_map.get(code, "UNKNOWN")
