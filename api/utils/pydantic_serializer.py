"""
Утиліти для серіалізації SQLAlchemy моделей через Pydantic
"""
from typing import List, Type, TypeVar, Dict, Any, Optional, Union
from pydantic import BaseModel

def model_to_dict(obj, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Перетворює SQLAlchemy модель в словник, готовий для JSON
    Функція для заміни методу to_dict()
    """
    if not obj:
        return {}
        
    if hasattr(obj, '__table__'):
        # Це SQLAlchemy модель
        exclude_set = set(exclude or [])
        result = {}
        for column in obj.__table__.columns:
            if column.name not in exclude_set:
                result[column.name] = getattr(obj, column.name)
        
        # Додаємо відносини, якщо вони вже завантажені
        for relationship_name, relationship in obj.__mapper__.relationships.items():
            if relationship_name not in exclude_set:
                relationship_value = getattr(obj, relationship_name)
                if relationship_value is not None:
                    if hasattr(relationship_value, '__iter__') and not isinstance(relationship_value, str):
                        result[relationship_name] = [model_to_dict(item) for item in relationship_value]
                    else:
                        result[relationship_name] = model_to_dict(relationship_value)
        
        return result
    
    # Для інших типів
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() 
                if not k.startswith('_') and k not in (exclude or [])}
    
    return obj


class ModelResponse(BaseModel):
    """Базовий клас для всіх відповідей API з моделей БД"""
    
    @classmethod
    def from_orm(cls, orm_obj):
        """Створює об'єкт Pydantic з ORM об'єкту"""
        if not orm_obj:
            return None
        return cls.model_validate(orm_obj)
    
    @classmethod
    def from_orm_list(cls, orm_list):
        """Створює список об'єктів Pydantic з списку ORM об'єктів"""
        if not orm_list:
            return []
        return [cls.from_orm(obj).model_dump() for obj in orm_list]

    
def serialize_model(orm_obj: Any, schema_cls: Type[ModelResponse] = None) -> Union[Dict, List[Dict]]:
    """
    Серіалізує ORM об'єкт або список об'єктів
    
    Аргументи:
        orm_obj: Об'єкт моделі SQLAlchemy або список таких об'єктів
        schema_cls: Клас Pydantic схеми для серіалізації
    
    Приклад:
        # Без схеми - використовується model_to_dict
        user_data = serialize_model(user)
        
        # З схемою - використовується schema_cls.from_orm
        user_data = serialize_model(user, UserResponse)
    """
    if orm_obj is None:
        return None
        
    # Для списку об'єктів
    if hasattr(orm_obj, '__iter__') and not isinstance(orm_obj, (str, dict)):
        if not orm_obj:
            return []
            
        # З використанням схеми
        if schema_cls:
            return schema_cls.from_orm_list(orm_obj)
            
        # Без схеми
        return [model_to_dict(item) for item in orm_obj]
    
    # Для одиночного об'єкту
    if schema_cls:
        return schema_cls.from_orm(orm_obj).model_dump()
    
    return model_to_dict(orm_obj)
