import re
from mydb import db, text
from func import cfg
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
            # print(f"""def do_sql_cmd: error exec sql:\n{e}\n{sql}""")
            return {"rowcount": -1, "data": f"{e}"}
    elif re.search(r"^select|^with", sql, re.I):
        try:
            res = db.engine.execute(text(sql), data)
            return {"rowcount": res.rowcount, "data": res.fetchall()}
        except Exception as e:
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
        return [{"rowcount": -1, "data": f"{e}"}]


def get_item_data(item_id=0):
    sql = f"""SELECT a.id,brand,sub_model,color_ua,ram,rom
,currPrice(price_val,(select zn from curr_kurs_val limit 1),a.status,percent,sum_pok_my) as sum_pok_my
,a.status,concat(brand,' ',sub_model) as name,battery,ekran,proc,rozmir,vaga,
concat('https://kit-gadget.com.ua/img/',lcase(replace(brand,' ','_')),'/',lcase(REPLACE(sub_model,' ','_')),'/',lcase(color_cat),'/tn_001.jpg') as img,
round((sum_pok_my/100),0)*2+20 as sum_ship2,round(sum_pok_my*0.005,0)+50 as sum_ship,
b.name4site as status_name,b.when_ship
FROM `TABLE 4` a
left join spr_status b on a.status=b.status
WHERE a.id=:item_id 
"""
    return do_sql_cmd(sql, {"item_id": item_id})


def send_telegram(
    text, parse_mode="", chat_id_in="vik", bot4send="tel", chat_id_4send="vik"
):
    # for telegram
    telcfg = cfg["tel"]
    tokens = chat_ids = {}

    tokens["tel"] = telcfg["tel_token"]
    tokens["track"] = telcfg["token_track_bot"]
    tokens["orders"] = telcfg["token_orders_bot"]
    tokens["sms"] = telcfg["token_sms_bot"]
    chat_ids["vik"] = telcfg["chat_id_vik"]
    chat_ids["tato"] = telcfg["chat_id_tato"]

    token = tokens[bot4send]
    chat_id_4send = chat_ids[chat_id_in]

    if parse_mode == "":
        parse_mode = "html"
    elif parse_mode == "text":
        parse_mode = ""

    url = f"""https://api.telegram.org/bot{token}/sendMessage"""

    import requests

    data = {
        "chat_id": chat_id_4send,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": "True",
    }

    try:
        r = requests.post(url, data=data)
    except Exception as e:
        with open("error_send_tel.log", "a", encoding="utf-8") as f:
            f.write(f"""Error requests.post(url: {url},data={data}).\n Error: {e}\n""")

    status_code, content = int(r.status_code), r.content

    if status_code != 200:
        with open("error_send_tel.log", "a", encoding="utf-8") as f:
            f.write(
                f"""error send:\nstatus_code: {status_code}, content:{content}\nurl:{url}\ndata:{data}\n"""
            )

    return status_code, content
