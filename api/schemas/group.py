"""
Схеми для роботи з групами
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GroupInvitationCreate(BaseModel):
    """Схема для створення запрошення до групи"""
    email: Optional[str] = None
    expires: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "expires": "2025-06-11T23:24:16+00:00"
            }
        }

class GroupUserUpdate(BaseModel):
    """Схема для оновлення інформації про користувача в групі"""
    role: Optional[str] = None
    relation_type: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "role": "member",
                "relation_type": "family"
            }
        }
