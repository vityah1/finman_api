from os import environ
import dotenv

dotenv.load_dotenv()

SECRET_KEY = environ["SECRET_KEY"]
JWT_SECRET_KEY = SECRET_KEY
SQLALCHEMY_DATABASE_URI = environ["DATABASE_URI"]
MONO_API_URL = "https://api.monobank.ua"

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
    "car": {
        "first_probig": "181299км;0л",
    },
    "Category": [
        ["Авто та АЗС", "Мийка", "Оплата консултационных услуг wayforpay"],
        ["Авто та АЗС", "Мийка", "WFP.CONSULT1"],
        ["Авто та АЗС", "Заправка", "OKKO"],
        ["Авто та АЗС", "Заправка", "FOP GABLOVSKYI M.V."],
        ["Авто та АЗС", "Заправка", "WOG"],
    ],
    "isDeleted": [["Portmone", "olx"], ["Укрпошта", "мито"]],
}


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
