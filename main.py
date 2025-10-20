import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Імпортуємо конфігурацію
from app.config import logger_config, SQLALCHEMY_DATABASE_URI
from models.models import SprCurrency
from mydb import db
from models import *
from fastapi_sqlalchemy import DBSessionMiddleware

# Налаштовуємо логування
logging.config.dictConfig(logger_config)
logger = logging.getLogger(__name__)

# Запуск на старті через lifespan контекст
from api.config.funcs import check_and_fill_spr_config_table, check_exsists_table
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Створюємо таблиці якщо вони не існують
    if not check_exsists_table(SprConfigTypes):
        db.create_all()
    check_result = check_and_fill_spr_config_table()
    if not check_result:
        raise Exception('Config table not valid')
    if not check_exsists_table(SprCurrency):
        SprCurrency.__table__.create(db.engine)

    yield  # Тут виконується програма

    # Код для виконання при завершенні (тут можна закрити ресурси)

# Створюємо екземпляр FastAPI з підтримкою OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2

# Налаштування схеми OAuth2 для Swagger UI
oauth2_scheme = OAuth2(
    flows=OAuthFlowsModel(
        password={
            "tokenUrl": "/api/auth/signin",
            "scopes": {}
        }
    ),
    description="JWT автентифікація"
)

app = FastAPI(
    title="FinMan API",
    version="1.0.0",
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "useBasicAuthenticationWithAccessCodeGrant": True
    },
    lifespan=lifespan
)

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Дозволяємо всім доменам
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DBSessionMiddleware для управління сесіями через ContextVar
app.add_middleware(
    DBSessionMiddleware,
    db_url=SQLALCHEMY_DATABASE_URI,
    engine_args={
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 10,
    },
)

# Імпортуємо та включаємо роутери
from api.config.route import router as config_router
from auth.auth import router as auth_router
from api.api import router as api_router
from api.mono.route import router as mono_router
from api.mono_users.route import router as mono_users_router
from api.sprs.route import router as sprs_router
from api.categories.route import router as categories_router
from api.payments.route import router as payments_router
from api.groups.route import router as groups_router
from api.invitations.route import router as invitations_router
from api.import_route import router as import_router
from api.utilities.route import router as utilities_router

# Підключаємо маршрути
# IMPORTANT: invitations_router must be registered before api_router and mono_router
# to avoid path conflicts with /api/users/{user_id} routes
app.include_router(config_router)
app.include_router(auth_router)
app.include_router(invitations_router)
app.include_router(api_router)
app.include_router(payments_router)
app.include_router(mono_router)
app.include_router(mono_users_router)
app.include_router(sprs_router)
app.include_router(categories_router)
app.include_router(groups_router)
app.include_router(import_router)
app.include_router(utilities_router)

# Підключаємо обробники помилок
from app.exceptions import register_exception_handlers
register_exception_handlers(app)

# OLD: Middleware для логування запитів та сесій БД (replaced by DBSessionMiddleware)
# @app.middleware("http")
# async def session_and_logging_middleware(request, call_next):
#     from mydb import db_session
#
#     try:
#         # Логуємо запит
#         logger.info(f"Request: {request.method} {request.url.path} | Headers: {request.headers}")
#
#         # Обробляємо запит
#         response = await call_next(request)
#
#         # Логуємо відповідь
#         logger.info(f"Response: {request.method} {request.url.path} | Status: {response.status_code}")
#
#         return response
#     finally:
#         # Закриваємо сесію після кожного запиту
#         db_session.remove()

# Middleware для логування запитів
@app.middleware("http")
async def logging_middleware(request, call_next):
    # Логуємо запит
    logger.info(f"Request: {request.method} {request.url.path} | Headers: {request.headers}")

    # Обробляємо запит
    response = await call_next(request)

    # Логуємо відповідь
    logger.info(f"Response: {request.method} {request.url.path} | Status: {response.status_code}")

    return response

# Запуск додатку (якщо викликається напряму)
if __name__ == "__main__":
    # Запускаємо uvicorn з підвищеним рівнем логування
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8090,
        reload=True,
        log_level="debug"
    )
