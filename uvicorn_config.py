"""
Конфігурація Uvicorn для запуску FastAPI додатку
"""
from typing import List, Dict, Any
import multiprocessing
import os

# Кількість процесів для обробки запитів (за замовчуванням - кількість CPU ядер)
workers_per_core_str = os.getenv("WORKERS_PER_CORE", "1")
max_workers_str = os.getenv("MAX_WORKERS", str(multiprocessing.cpu_count() * 2))
use_max_workers = None
if max_workers_str:
    use_max_workers = int(max_workers_str)
web_concurrency_str = os.getenv("WEB_CONCURRENCY", None)

# Налаштування хоста і порту
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8090")

# Налаштування для логування
log_level = os.getenv("LOG_LEVEL", "info")
log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
    },
}

# Налаштування додаткових параметрів
reload = os.getenv("RELOAD", "False").lower() in ("true", "1", "t")
reload_dirs = os.getenv("RELOAD_DIRS", ".").split(",")
reload_includes = os.getenv("RELOAD_INCLUDES", "*.py").split(",")
reload_excludes = os.getenv("RELOAD_EXCLUDES", ".git,__pycache__").split(",")

# SSL налаштування
ssl_keyfile = os.getenv("SSL_KEYFILE", None)
ssl_certfile = os.getenv("SSL_CERTFILE", None)

# Загальні налаштування додатку
app_name = "runserver:app"
