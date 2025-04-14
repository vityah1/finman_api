# _*_ coding:UTF-8 _*_

from fastapi import APIRouter, Depends
from app.jwt import get_current_user
from pydantic import BaseModel
from typing import Optional, List

from api.config.services import (
    get_user_config_,
    get_config_,
    add_config_,
    edit_config_,
    delete_config_,
    get_config_types_,
)

router = APIRouter(prefix="/api/config", tags=["config"])

class ConfigOut(BaseModel):
    id: int
    user_id: int
    type_data: str
    value_data: Optional[str] = None
    add_value: Optional[str] = None

class ConfigListResponse(BaseModel):
    data: List[ConfigOut]

class ConfigResponse(BaseModel):
    data: ConfigOut

class StatusOkResponse(BaseModel):
    result: str

@router.get("/config_types", response_model=List[str])
def get_config_types():
    types = get_config_types_()
    return [t['type_data'] for t in types]

@router.get("/users/config", response_model=ConfigListResponse)
def get_user_config(user_id: str = Depends(get_current_user)):
    configs = get_user_config_(user_id)
    return ConfigListResponse(data=[ConfigOut(**c) for c in configs])

@router.post("/users/config", response_model=ConfigListResponse)
def add_config(user_id: str = Depends(get_current_user)):
    configs = add_config_(user_id)
    return ConfigListResponse(data=[ConfigOut(**c) for c in configs])

@router.delete("/{config_id}", response_model=StatusOkResponse)
def delete_config(config_id: int, user_id: str = Depends(get_current_user)):
    res = delete_config_(config_id)
    return StatusOkResponse(**res)

@router.patch("/{config_id}", response_model=ConfigResponse)
def edit_config(config_id: int, user_id: str = Depends(get_current_user)):
    config = edit_config_(config_id)
    return ConfigResponse(data=ConfigOut(**config))

@router.get("/{config_id}", response_model=ConfigResponse)
def get_config(config_id: int, user_id: str = Depends(get_current_user)):
    config = get_config_(config_id)
    return ConfigResponse(data=ConfigOut(**config))
