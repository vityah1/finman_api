import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import List

# Імпортуємо конфігурацію
from app.config import logger_config
from models.models import SprCurrency
from mydb import db
from models import *

# Налаштовуємо логування
logging.config.dictConfig(logger_config)
logger = logging.getLogger(__name__)

# Створюємо екземпляр FastAPI
app = FastAPI(title="FinMan API", version="1.0.0")

# Додаємо CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Імпортуємо та включаємо роутери
from api.config.route import router as config_router
from auth.auth import router as auth_router
from api.api import router as api_router
from api.mono.route import router as mono_router
from api.mono_users.route import router as mono_users_router
from api.sprs.route import router as sprs_router
from api.revolut.route import router as revolut_router
from api.wise.route import router as wise_router
from api.p24.route import router as p24_router
from api.categories.route import router as categories_router
from api.payments.route import router as payments_router
from api.groups.route import router as groups_router
from api.invitations.route import router as invitations_router

# Підключаємо маршрути
app.include_router(config_router)
app.include_router(auth_router)
app.include_router(api_router)
app.include_router(payments_router)
app.include_router(mono_router)
app.include_router(mono_users_router)
app.include_router(sprs_router)
app.include_router(revolut_router)
app.include_router(wise_router)
app.include_router(p24_router)
app.include_router(categories_router)
app.include_router(groups_router)
app.include_router(invitations_router)

# Підключаємо обробники помилок
from app.exceptions import register_exception_handlers
register_exception_handlers(app)

# Запуск на старті
from api.config.funcs import check_and_fill_spr_config_table, check_exsists_table

@app.on_event("startup")
async def startup_db_client():
    # Створюємо таблиці якщо вони не існують
    if not check_exsists_table(SprConfigTypes):
        db.create_all()
    check_result = check_and_fill_spr_config_table()
    if not check_result:
        raise Exception('Config table not valid')
    if not check_exsists_table(SprCurrency):
        SprCurrency.__table__.create(db.engine)

# Відображення запитів у логах    
@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    logger.info(
        f"path: {request.url.path} | method: {request.method} | status: {response.status_code}"
    )
    return response

# Запуск додатку (якщо викликається напряму)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8090, reload=True)
