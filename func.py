import random
import datetime
import requests

from config import cfg


um_sub_cat = ""
if cfg.get("not_sub_cat"):
    um_sub_cat = f"""
    and sub_cat not in ('{"','".join(cfg.get("not_sub_cat"))}')
    """

um_cat = ""
if cfg.get("not_cat"):
    um_cat = f"""
    and cat not in ('{"','".join(cfg.get("not_cat"))}')
    """

um_not_my_expspense = f"""
{um_sub_cat}
{um_cat}
and `deleted`!=1
and suma>0
"""

cat4zam = """
if(sub_cat='Vdaliy Rik','Авто та АЗС',cat) as cat
"""


def mydatetime(par: str = None):
    if not par:
        return datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y %H:%M:%S")
    else:
        return datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d_%H%M%S")


def send_telegram(text: str, parce_mode: str = "HTML", chat_id_in: str = "", token: str = "", chat_id_4send: str = ""):
    # for telegram
    # myLog(f"token: {token}")

    url = "https://api.telegram.org/bot{}/sendMessage".format(
        cfg["telegram"]["tokens"].get(f"{token}_bot", "tel_token")
    )
    # myLog(f"url: {url}")
    data = {
        "chat_id": cfg["telegram"]["chat_ids"].get(chat_id_in, cfg["telegram"]["chat_ids"].get("vik")),
        "text": text,
        "parse_mode": parce_mode,
        "disable_web_page_preview": "True",
    }

    r = requests.post(url, data=data)

    status_code, content = str(r.status_code), r.reason

    if status_code != 200:
        with open("send_tel.log", "a", encoding="utf-8") as f:
            f.write(
                f"""{mydatetime()}
error send:\nstatus_code: {status_code}, content:{content}
url:{url}
data:{data}
chat_id: [{chat_id_4send}]\n\n"""
            )

    return status_code, content


rand = random.random() * 10000000
