from fastapi import APIRouter

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from fastapi_jwt import JwtAuthorizationCredentials
from api.config.services import (
    get_user_config_,
    get_config_,
    add_config_,
    edit_config_,
    delete_config_,
    get_config_types_,
)

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/config_types")
def get_config_types():
    return get_config_types_()

# Локальний імпорт jwt_bearer для уникнення циклічного імпорту
@router.get("/users/config")
def get_user_config(credentials: JwtAuthorizationCredentials = Depends(lambda: __import__('app').app.jwt_bearer)):
    jwt_bearer = __import__('app').app.jwt_bearer
    credentials = jwt_bearer()
    user_id = credentials["sub"]["user_id"] if isinstance(credentials["sub"], dict) else credentials["sub"]
    return get_user_config_(user_id)

@router.post("/users/config")
def add_config(credentials: JwtAuthorizationCredentials = Depends(lambda: __import__('app').app.jwt_bearer)):
    jwt_bearer = __import__('app').app.jwt_bearer
    credentials = jwt_bearer()
    user_id = credentials["sub"]["user_id"] if isinstance(credentials["sub"], dict) else credentials["sub"]
    return add_config_(user_id)

@router.delete("/config/{config_id}")
def delete_config(config_id: int, credentials: JwtAuthorizationCredentials = Depends(lambda: __import__('app').app.jwt_bearer)):
    return delete_config_(config_id)

@router.patch("/config/{config_id}")
def edit_config(config_id: int, credentials: JwtAuthorizationCredentials = Depends(lambda: __import__('app').app.jwt_bearer)):
    return edit_config_(config_id)

@router.get("/config/{config_id}")
def get_config(config_id: int, credentials: JwtAuthorizationCredentials = Depends(lambda: __import__('app').app.jwt_bearer)):
    return get_config_(config_id)
