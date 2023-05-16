from os import environ
import dotenv

dotenv.load_dotenv()

api_url = environ.get("BASE_API")
mono_webhook = environ.get("MONO_WEBHOOK")
vik_token = environ.get("VIK_MONO_TOKEN")
vik_account = environ.get("VIK_MONO_ACCOUNT")

tanya_token = environ.get("TANYA_MONO_TOKEN")
tanya_account = environ.get("TANYA_MONO_ACCOUNT")

tel_token = environ.get("TEL_TOKEN")
token_tel_bot = environ.get("TOKEN_TEL_BOT")
token_track_bot = environ.get("TOKEN_TRACK_BOT")
token_orders_bot = environ.get("TOKEN_ORDERS_BOT")
token_sms_bot = environ.get("TOKEN_SMS_BOT")
token_new_bot = environ.get("TOKEN_NEW_BOT")
token_gsm_bot = environ.get("TOKEN_GSM_BOT")
token_monitor_bot = environ.get("TOKEN_MONITOR_BOT")
token_bank_bot = environ.get("TOKEN_BANK_BOT")
chat_id_vik = environ.get("CHAT_ID_VIK")
chat_id_tato = environ.get("CHAT_ID_TATO")

api_url = environ.get("BASE_API")


cfg = {
    "dict_phones": {
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
    },
    "not_sub_cat": [
        "AliExpress",
        "PAYPAL",
        "PSP*mall.my.com",
        "PAYPAL *GEEKBUYING",
        "LIQPAY*Hosting Ukrayin",
        "Pandao",
        "Укрпошта",
        "Нова пошта",
        "portmone.com.ua",
        "monobank",
        "DHGATE",
        "DHGATE.COM",
        "wondershare",
    ],
    "not_cat": [],
    "not_cat_": ["Грошові перекази"],
    # "webhook": "https://kt.if.ua/cgi-bin/pwa/get_mono_webhook.py",
    "webhook": f"{api_url}/api/mono/webhook",
    "webhook_gapps": "https://script.google.com/macros/s/AKfycbxq8R2y9ugmDmfYDAp9rf5MEUs_5lf2SNT_Cc0u_R3KYTfYMPvc/exec",
    "mono": {
        "users": [
            {"name": "vik", "token": vik_token, "account": [vik_account, "ZLzex3Bs5Cki9ksmcKijgg"]},
            {"name": "tanya", "token": tanya_token, "account": [tanya_account]},
        ]
    },
    "telegram": {
        "tokens": {
            "tel": tel_token,
            "tel_bot": token_tel_bot,
            "track_bot": token_track_bot,
            "orders_bot": token_orders_bot,
            "sms_bot": token_sms_bot,
            "new_bot": token_new_bot,
            "gsm_bot": token_gsm_bot,
            "monitor_bot": token_monitor_bot,
            "bank_bot": token_bank_bot,
        },
        "chat_ids": {
            "vik": chat_id_vik,
            "tato": chat_id_tato,
        },
    },
    "car": {
        "first_probig": "181299км;0л",
    },
    "CurrencyCode": {"980": "грн", "840": "USD", "978": "EUR"},
    "Category": [
        ["Авто та АЗС", "Мийка", "Оплата консултационных услуг wayforpay"],
        ["Авто та АЗС", "Мийка", "WFP.CONSULT1"],
        ["Авто та АЗС", "Заправка", "OKKO"],
        ["Авто та АЗС", "Заправка", "FOP GABLOVSKYI M.V."],
        ["Авто та АЗС", "Заправка", "WOG"],
    ],
    "isDeleted": [["Portmone", "olx"], ["Укрпошта", "мито"]],
}

cfg["SECRET_KEY"] = environ["SECRET_KEY"]
cfg["DATABASE_URI"] = environ["DATABASE_URI"]

webhook = cfg["webhook"]
users = cfg["mono"]["users"]
CurrencyCode = cfg["CurrencyCode"]

mono_api_url = "https://api.monobank.ua"

logger_config = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        },
        # "file": {
        #     "class": "logging.FileHandler",
        #     "filename": "finman.log",
        #     "formatter": "default",
        # },
        "size-rotate": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "finman.log",
            "maxBytes": 1000000,
            "backupCount": 5,
            "formatter": "default",
        },
        "mono": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "mono.log",
            "maxBytes": 1000000,
            "backupCount": 5,
            "formatter": "default",
        },
        "telegram": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "telegram.log",
            "maxBytes": 1000000,
            "backupCount": 5,
            "formatter": "default",
        },
        # "time-rotate": {
        #     "class": "logging.handlers.TimedRotatingFileHandler",
        #     "filename": "flask.log",
        #     "when": "D",
        #     "interval": 10,
        #     "backupCount": 5,
        #     "formatter": "default",
        # },
    },
    "root": {"level": "DEBUG", "handlers": ["console", "size-rotate"]},
    "loggers": {
        "mono": {
            "level": "INFO",
            "handlers": ["mono"],
            "propagate": False,
        },
        "telegram": {
            "level": "INFO",
            "handlers": ["telegram"],
            "propagate": False,
        }
    }
}
