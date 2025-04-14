from os import environ
import dotenv
import sys

# Спробуємо знайти .env файл
print("Пошук файлу .env...")
dotenv_path = dotenv.find_dotenv()
if dotenv_path:
    print(f"Знайдено .env файл: {dotenv_path}")
    dotenv.load_dotenv(dotenv_path)
else:
    print("УВАГА: Файл .env не знайдено, використовуємо лише системні змінні середовища", file=sys.stderr)
    dotenv.load_dotenv()

# Перевіряємо наявність змінних середовища
print("Перевірка змінних середовища...")
required_vars = ["SECRET_KEY", "DATABASE_URI"]
missing_vars = [var for var in required_vars if var not in environ]

if missing_vars:
    print(f"УВАГА: Відсутні наступні змінні середовища: {', '.join(missing_vars)}", file=sys.stderr)
    # Встановлюємо значення за замовчуванням для відсутніх змінних
    if "SECRET_KEY" not in environ:
        environ["SECRET_KEY"] = "default_secret_key_for_development_only"
        print("Встановлено SECRET_KEY за замовчуванням (тільки для розробки)", file=sys.stderr)
    if "DATABASE_URI" not in environ:
        environ["DATABASE_URI"] = "sqlite:///./finman.db"
        print("Встановлено DATABASE_URI за замовчуванням на локальну SQLite", file=sys.stderr)
else:
    print("Усі необхідні змінні середовища знайдено")

# Визначення основних змінних
SECRET_KEY = environ["SECRET_KEY"]
JWT_SECRET_KEY = SECRET_KEY
SQLALCHEMY_DATABASE_URI = environ["DATABASE_URI"]
MONO_API_URL = "https://api.monobank.ua"

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
