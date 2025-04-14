from logging.config import dictConfig

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging.config import dictConfig
from app.config import logger_config
from models.models import SprCurrency
from mydb import db
from models import *

from api.config import router as config_router
from auth.auth import router as auth_router
from api.api_fastapi import router as api_payments_router
from api.mono import router as mono_router
from api.mono_users import router as mono_users_router
from api.sprs import router as sprs_router
from api.revolut import router as revolut_router
from api.wise import router as wise_router
from api.p24 import router as p24_router
from api.categories import router as categories_router
from api.payments import router as payments_router
from api.groups import router as groups_router
from api.invitations.route import router as invitations_router
from api.utilities.api import router as utilities_router

# Logging
dictConfig(logger_config)

app = FastAPI(title="Finman API", docs_url="/docs", redoc_url="/redoc")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Config (configure via settings or config.py)
# @AuthJWT.load_config
def get_config():
    from app.config import Settings
    return Settings()

# Підключення бази даних для FastAPI
from app.database import engine, Base

# Якщо потрібно створити таблиці при старті (опціонально)
# Base.metadata.create_all(bind=engine)

# Routers registration
app.include_router(config_router)
app.include_router(auth_router)
app.include_router(api_payments_router)
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
app.include_router(utilities_router)

from api.config.funcs import check_and_fill_spr_config_table, check_exsists_table
from app.database import engine, Base

Base.metadata.create_all(bind=engine)
check_result = check_and_fill_spr_config_table()
if not check_result:
    raise Exception('Config table not valid')
SprCurrency.__table__.create(bind=engine, checkfirst=True)


def __repr__(self):
    return "<Mysession %r" % self.id


    return response


import logging
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("uvicorn.access")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    response: Response = await call_next(request)
    logger.info(
        "path: %s | method: %s | status: %s | size: %s",
        request.url.path,
        request.method,
        response.status_code,
        response.headers.get("content-length", "-")
    )
    return response


from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": f"Not Found: {request.url.path}"})
