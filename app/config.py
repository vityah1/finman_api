from os import environ
import dotenv
from typing import Dict, Any

dotenv.load_dotenv()

# Основні налаштування додатку
SECRET_KEY = environ["SECRET_KEY"]
JWT_SECRET_KEY = SECRET_KEY
SQLALCHEMY_DATABASE_URI = environ["DATABASE_URI"]
MONO_API_URL = "https://api.monobank.ua"
DEBUG = environ.get("DEBUG", "False").lower() in ("true", "1", "t")

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
