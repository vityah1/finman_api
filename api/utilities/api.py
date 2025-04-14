from fastapi import APIRouter, Depends, HTTPException
from app.jwt import get_current_user
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
import datetime

from models import (
    SprUtilityType, UtilityMeter, UtilityTariff, UtilityMeterReading,
    User, Group, UserGroupAssociation
)
from api.schemas import (
    UtilityTypeData, UtilityMeterData, UtilityTariffData, UtilityMeterReadingData
)
from mydb import db
from utils import do_sql_sel

router = APIRouter(prefix="/api/utilities", tags=["utilities"])


# Функція для перевірки доступу користувача до групи
def check_group_access(user_id, group_id):
    if not group_id:
        return True
    
    association = UserGroupAssociation.query.filter(
        and_(
            UserGroupAssociation.user_id == user_id,
            UserGroupAssociation.group_id == group_id
        )
    ).first()
    
    return association is not None


# Функція для визначення ресурсів доступних користувачу
def get_user_resources(user_id, model_class, include_group_resources=True):
    # Запит для об'єктів, які безпосередньо належать користувачу
    user_resources = model_class.query.filter(model_class.user_id == user_id)
    
    if include_group_resources:
        # Отримуємо ID груп, до яких належить користувач
        user_groups = UserGroupAssociation.query.filter(
            UserGroupAssociation.user_id == user_id
        ).with_entities(UserGroupAssociation.group_id).all()
        
        group_ids = [group.group_id for group in user_groups]
        
        if group_ids:
            # Запит для об'єктів, які належать групам користувача
            group_resources = model_class.query.filter(
                model_class.group_id.in_(group_ids)
            )
            
            # Об'єднуємо результати
            return user_resources.union(group_resources)
    
    return user_resources


# API для типів комунальних послуг

from fastapi import Body

from typing import List
from api.schemas import UtilityTypeData
from pydantic import BaseModel
from typing import Optional

# --- Pydantic Response Schemas (перенесено вгору для уникнення NameError) ---
class UtilityTypeOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    user_id: int | None = None
    group_id: int | None = None
    created: str | None = None
    updated: str | None = None

class UtilityTypeDataOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    created: Optional[str] = None
    updated: Optional[str] = None

class StatusDataResponse(BaseModel):
    status: str
    data: UtilityTypeDataOut

class StatusOkResponse(BaseModel):
    status: str

class UtilityMeterOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    utility_type_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None
    serial_number: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

class StatusDataListResponse(BaseModel):
    status: str
    data: List[UtilityMeterOut]

class StatusErrorResponse(BaseModel):
    status: str
    message: str

# --- Tariff ---
class UtilityTariffOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    utility_type_id: int
    rate: float
    currency: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    tariff_type: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None

class StatusTariffListResponse(BaseModel):
    status: str
    data: List[UtilityTariffOut]

class StatusTariffResponse(BaseModel):
    status: str
    data: UtilityTariffOut

# --- Meter Reading ---
class UtilityMeterReadingOut(BaseModel):
    id: int
    meter_id: int
    reading_date: Optional[str] = None
    reading_value: float
    previous_reading_id: Optional[int] = None
    consumption: Optional[float] = None
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    tariff_id: Optional[int] = None
    image_url: Optional[str] = None
    month: int
    year: int
    cost: Optional[float] = None
    created: Optional[str] = None
    updated: Optional[str] = None

class StatusReadingListResponse(BaseModel):
    status: str
    data: List[UtilityMeterReadingOut]

class StatusReadingResponse(BaseModel):
    status: str
    data: UtilityMeterReadingOut

# --- Statistics ---
class MeterStatisticsOut(BaseModel):
    month: int
    year: int
    reading_value: Optional[float] = None
    consumption: Optional[float] = None
    cost: Optional[float] = None

class TypeStatisticsOut(BaseModel):
    month: int
    year: int
    total_consumption: float
    total_cost: float

class StatusMeterStatisticsResponse(BaseModel):
    status: str
    data: List[MeterStatisticsOut]

class StatusTypeStatisticsResponse(BaseModel):
    status: str
    data: List[TypeStatisticsOut]
# --- END Schemas ---

@router.get("/types", response_model=List[UtilityTypeOut])
def get_utility_types(user_id: str = Depends(get_current_user)):
    utility_types = get_user_resources(user_id, SprUtilityType).all()
    return [
        UtilityTypeOut(
            id=ut.id,
            name=ut.name,
            description=ut.description,
            user_id=ut.user_id,
            group_id=ut.group_id,
            created=ut.created.isoformat() if ut.created else None,
            updated=ut.updated.isoformat() if ut.updated else None
        ) for ut in utility_types
    ]

@router.post("/types", response_model=StatusDataResponse)
def create_utility_type(body: UtilityTypeData = Body(...), user_id: str = Depends(get_current_user)):
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    if not body.group_id and not body.user_id:
        body.user_id = user_id
    try:
        utility_type = SprUtilityType(**body.dict())
        db.session.add(utility_type)
        db.session.commit()
        return StatusDataResponse(
            status="ok",
            data=UtilityTypeDataOut(
                id=utility_type.id,
                name=utility_type.name,
                description=utility_type.description,
                user_id=utility_type.user_id,
                group_id=utility_type.group_id,
                created=utility_type.created.isoformat(),
                updated=utility_type.updated.isoformat() if utility_type.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

@router.get("/types/{type_id}", response_model=StatusDataResponse)
def get_utility_type(type_id: int, user_id: str = Depends(get_current_user)):
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not utility_type:
        raise HTTPException(404, detail="Тип комунальної послуги не знайдено")
    return StatusDataResponse(
        status="ok",
        data=UtilityTypeDataOut(
            id=utility_type.id,
            name=utility_type.name,
            description=utility_type.description,
            user_id=utility_type.user_id,
            group_id=utility_type.group_id,
            created=utility_type.created.isoformat(),
            updated=utility_type.updated.isoformat() if utility_type.updated else None
        )
    )

@router.put("/types/{type_id}", response_model=StatusDataResponse)
def update_utility_type(type_id: int, body: UtilityTypeData = Body(...), user_id: str = Depends(get_current_user)):
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not utility_type:
        raise HTTPException(404, detail="Тип комунальної послуги не знайдено")
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    try:
        utility_type.name = body.name
        utility_type.description = body.description
        utility_type.user_id = body.user_id
        utility_type.group_id = body.group_id
        db.session.commit()
        return StatusDataResponse(
            status="ok",
            data=UtilityTypeDataOut(
                id=utility_type.id,
                name=utility_type.name,
                description=utility_type.description,
                user_id=utility_type.user_id,
                group_id=utility_type.group_id,
                created=utility_type.created.isoformat(),
                updated=utility_type.updated.isoformat() if utility_type.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

@router.delete("/types/{type_id}")
def delete_utility_type(type_id: int, user_id: str = Depends(get_current_user)):
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not utility_type:
        raise HTTPException(404, detail="Тип комунальної послуги не знайдено")
    meters = UtilityMeter.query.filter_by(utility_type_id=type_id).count()
    tariffs = UtilityTariff.query.filter_by(utility_type_id=type_id).count()
    if meters > 0 or tariffs > 0:
        raise HTTPException(400, detail="Неможливо видалити тип комунальної послуги, до якого прив'язані лічильники або тарифи")

@router.delete("/types/{type_id}", response_model=StatusOkResponse)
def delete_utility_type(type_id: int, user_id: str = Depends(get_current_user)):
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not utility_type:
        raise HTTPException(404, detail="Тип комунальної послуги не знайдено")
    meters = UtilityMeter.query.filter_by(utility_type_id=type_id).count()
    tariffs = UtilityTariff.query.filter_by(utility_type_id=type_id).count()
    if meters > 0 or tariffs > 0:
        raise HTTPException(400, detail="Неможливо видалити тип комунальної послуги, до якого прив'язані лічильники або тарифи")
    try:
        db.session.delete(utility_type)
        db.session.commit()
        return StatusOkResponse(status="ok")
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

@router.put("/api/utilities/types/{type_id}")
async def update_utility_type(type_id, body: UtilityTypeData, user_id: str = Depends(get_current_user)):
   
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not utility_type:
        raise HTTPException(404, detail="Тип комунальної послуги не знайдено")
    
    # Перевірка доступу до групи
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    
    try:
        utility_type.name = body.name
        utility_type.description = body.description
        utility_type.user_id = body.user_id
        utility_type.group_id = body.group_id
        
        db.session.commit()
        
        return StatusDataResponse(
            status="ok",
            data=UtilityTypeDataOut(
                id=utility_type.id,
                name=utility_type.name,
                description=utility_type.description,
                user_id=utility_type.user_id,
                group_id=utility_type.group_id,
                created=utility_type.created.isoformat(),
                updated=utility_type.updated.isoformat() if utility_type.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

@router.delete("/api/utilities/types/{type_id}")
async def delete_utility_type(type_id, user_id: str = Depends(get_current_user)):
   
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not utility_type:
        raise HTTPException(404, detail="Тип комунальної послуги не знайдено")
    
    try:
        # Перевіряємо, чи є прив'язані лічильники чи тарифи
        meters = UtilityMeter.query.filter_by(utility_type_id=type_id).count()
        tariffs = UtilityTariff.query.filter_by(utility_type_id=type_id).count()
        
        if meters > 0 or tariffs > 0:
            raise HTTPException(400, detail="Неможливо видалити тип комунальної послуги, до якого прив'язані лічильники або тарифи")
        
        db.session.delete(utility_type)
        db.session.commit()
        
        return StatusOkResponse(status="ok")
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

# API для лічильників
@router.get("/api/utilities/meters", response_model=StatusDataListResponse)
def get_utility_meters(user_id: str = Depends(get_current_user)):
    utility_type_id = request.args.get("utility_type_id")
    query = get_user_resources(user_id, UtilityMeter)
    if utility_type_id:
        query = query.filter(UtilityMeter.utility_type_id == utility_type_id)
    utility_meters = query.all()
    result = [
        UtilityMeterOut(
            id=meter.id,
            name=meter.name,
            description=meter.description,
            utility_type_id=meter.utility_type_id,
            user_id=meter.user_id,
            group_id=meter.group_id,
            is_active=meter.is_active,
            serial_number=meter.serial_number,
            created=meter.created.isoformat() if meter.created else None,
            updated=meter.updated.isoformat() if meter.updated else None
        ) for meter in utility_meters
    ]
    return StatusDataListResponse(status="ok", data=result)

@router.post("/api/utilities/meters", response_model=StatusDataResponse, responses={404: {"model": StatusErrorResponse}})
async def create_utility_meter(body: UtilityMeterData = Body(...), user_id: str = Depends(get_current_user)):
    # Перевірка доступу до групи
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    
    # Перевірка існування типу комунальної послуги
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == body.utility_type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not utility_type:
        return StatusErrorResponse(status="error", message="Тип комунальної послуги не знайдено")
    
    # Встановлюємо ID користувача, якщо він не вказаний
    if not body.group_id and not body.user_id:
        body.user_id = user_id
    
    try:
        meter = UtilityMeter(**body.dict())
        db.session.add(meter)
        db.session.commit()
        
        return StatusDataResponse(
            status="ok",
            data=UtilityMeterOut(
                id=meter.id,
                name=meter.name,
                description=meter.description,
                utility_type_id=meter.utility_type_id,
                user_id=meter.user_id,
                group_id=meter.group_id,
                is_active=meter.is_active,
                serial_number=meter.serial_number,
                created=meter.created.isoformat(),
                updated=meter.updated.isoformat() if meter.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

@router.get("/api/utilities/meters/<int:meter_id>", response_model=StatusDataResponse, responses={404: {"model": StatusErrorResponse}})
def get_utility_meter(meter_id, user_id: str = Depends(get_current_user)):
    current_user = user_id
    user_id = current_user.get('user_id')
    
    meter = UtilityMeter.query.filter(
        and_(
            UtilityMeter.id == meter_id,
            or_(
                UtilityMeter.user_id == user_id,
                UtilityMeter.id.in_(
                    db.session.query(UtilityMeter.id)
                    .join(Group, UtilityMeter.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not meter:
        return StatusErrorResponse(status="error", message="Лічильник не знайдено")
    return StatusDataResponse(
        status="ok",
        data=UtilityMeterOut(
            id=meter.id,
            name=meter.name,
            description=meter.description,
            utility_type_id=meter.utility_type_id,
            user_id=meter.user_id,
            group_id=meter.group_id,
            is_active=meter.is_active,
            serial_number=meter.serial_number,
            created=meter.created.isoformat(),
            updated=meter.updated.isoformat() if meter.updated else None
        )
    )

@router.put("/api/utilities/meters/<int:meter_id>", response_model=StatusDataResponse, responses={404: {"model": StatusErrorResponse}})
def update_utility_meter(meter_id, body: UtilityMeterData, user_id: str = Depends(get_current_user)):
    current_user = user_id
    user_id = current_user.get('user_id')
    
    meter = UtilityMeter.query.filter(
        and_(
            UtilityMeter.id == meter_id,
            or_(
                UtilityMeter.user_id == user_id,
                UtilityMeter.id.in_(
                    db.session.query(UtilityMeter.id)
                    .join(Group, UtilityMeter.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not meter:
        return StatusErrorResponse(status="error", message="Лічильник не знайдено")
    
    # Перевірка доступу до групи
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    
    # Перевірка існування типу комунальної послуги
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == body.utility_type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not utility_type:
        return StatusErrorResponse(status="error", message="Тип комунальної послуги не знайдено")
    
    try:
        meter.name = body.name
        meter.description = body.description
        meter.utility_type_id = body.utility_type_id
        meter.user_id = body.user_id
        meter.group_id = body.group_id
        meter.is_active = body.is_active
        meter.serial_number = body.serial_number
        
        db.session.commit()
        
        return StatusDataResponse(
            status="ok",
            data=UtilityMeterOut(
                id=meter.id,
                name=meter.name,
                description=meter.description,
                utility_type_id=meter.utility_type_id,
                user_id=meter.user_id,
                group_id=meter.group_id,
                is_active=meter.is_active,
                serial_number=meter.serial_number,
                created=meter.created.isoformat(),
                updated=meter.updated.isoformat() if meter.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise HTTPException(400, detail=str(e))

@router.delete("/api/utilities/meters/<int:meter_id>", response_model=StatusOkResponse, responses={404: {"model": StatusErrorResponse}, 400: {"model": StatusErrorResponse}})
def delete_utility_meter(meter_id, user_id: str = Depends(get_current_user)):
    current_user = user_id
    user_id = current_user.get('user_id')
    
    meter = UtilityMeter.query.filter(
        and_(
            UtilityMeter.id == meter_id,
            or_(
                UtilityMeter.user_id == user_id,
                UtilityMeter.id.in_(
                    db.session.query(UtilityMeter.id)
                    .join(Group, UtilityMeter.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    
    if not meter:
        return StatusErrorResponse(status="error", message="Лічильник не знайдено")
    
    try:
        # Перевіряємо, чи є показники для цього лічильника
        readings = UtilityMeterReading.query.filter_by(meter_id=meter_id).count()
        
        if readings > 0:
            return StatusErrorResponse(status="error", message="Неможливо видалити лічильник, для якого існують показники")
        
        db.session.delete(meter)
        db.session.commit()
        
        return StatusOkResponse(status="ok")
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

# API для тарифів
@router.get("/api/utilities/tariffs", response_model=StatusTariffListResponse)
def get_utility_tariffs(user_id: str = Depends(get_current_user)):
    utility_type_id = request.args.get("utility_type_id")
    tariff_type = request.args.get("tariff_type")
    include_expired = request.args.get("include_expired", "false").lower() == "true"
    query = get_user_resources(user_id, UtilityTariff)
    if utility_type_id:
        query = query.filter(UtilityTariff.utility_type_id == utility_type_id)
    if tariff_type:
        query = query.filter(UtilityTariff.tariff_type == tariff_type)
    if not include_expired:
        current_date = datetime.datetime.now(datetime.timezone.utc)
        query = query.filter(
            or_(
                UtilityTariff.valid_to.is_(None),
                UtilityTariff.valid_to > current_date
            )
        )
    tariffs = query.order_by(UtilityTariff.valid_from.desc()).all()
    result = [
        UtilityTariffOut(
            id=tariff.id,
            name=tariff.name,
            description=tariff.description,
            utility_type_id=tariff.utility_type_id,
            rate=tariff.rate,
            currency=tariff.currency,
            valid_from=tariff.valid_from.isoformat() if tariff.valid_from else None,
            valid_to=tariff.valid_to.isoformat() if tariff.valid_to else None,
            user_id=tariff.user_id,
            group_id=tariff.group_id,
            tariff_type=tariff.tariff_type,
            created=tariff.created.isoformat() if tariff.created else None,
            updated=tariff.updated.isoformat() if tariff.updated else None
        ) for tariff in tariffs
    ]
    return StatusTariffListResponse(status="ok", data=result)

@router.post("/api/utilities/tariffs", response_model=StatusTariffResponse, responses={400: {"model": StatusErrorResponse}, 404: {"model": StatusErrorResponse}})
def create_utility_tariff(body: UtilityTariffData, user_id: str = Depends(get_current_user)):
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == body.utility_type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not utility_type:
        return StatusErrorResponse(status="error", message="Тип комунальної послуги не знайдено")
    if not body.group_id and not body.user_id:
        body.user_id = user_id
    if not body.valid_from:
        body.valid_from = datetime.datetime.now(datetime.timezone.utc)
    try:
        if body.tariff_type:
            existing_tariffs = UtilityTariff.query.filter(
                and_(
                    UtilityTariff.utility_type_id == body.utility_type_id,
                    UtilityTariff.tariff_type == body.tariff_type,
                    or_(
                        UtilityTariff.valid_to.is_(None),
                        UtilityTariff.valid_to > body.valid_from
                    ),
                    or_(
                        and_(UtilityTariff.user_id == body.user_id, body.user_id != None),
                        and_(UtilityTariff.group_id == body.group_id, body.group_id != None)
                    )
                )
            ).all()
            for et in existing_tariffs:
                et.valid_to = body.valid_from
        tariff = UtilityTariff(**body.model_dump())
        db.session.add(tariff)
        db.session.commit()
        return StatusTariffResponse(
            status="ok",
            data=UtilityTariffOut(
                id=tariff.id,
                name=tariff.name,
                description=tariff.description,
                utility_type_id=tariff.utility_type_id,
                rate=tariff.rate,
                currency=tariff.currency,
                valid_from=tariff.valid_from.isoformat() if tariff.valid_from else None,
                valid_to=tariff.valid_to.isoformat() if tariff.valid_to else None,
                user_id=tariff.user_id,
                group_id=tariff.group_id,
                tariff_type=tariff.tariff_type,
                created=tariff.created.isoformat(),
                updated=tariff.updated.isoformat() if tariff.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

@router.get("/api/utilities/tariffs/<int:tariff_id>", response_model=StatusTariffResponse, responses={404: {"model": StatusErrorResponse}})
def get_utility_tariff(tariff_id, user_id: str = Depends(get_current_user)):
    current_user = user_id
    user_id = current_user.get('user_id')
    tariff = UtilityTariff.query.filter(
        and_(
            UtilityTariff.id == tariff_id,
            or_(
                UtilityTariff.user_id == user_id,
                UtilityTariff.id.in_(
                    db.session.query(UtilityTariff.id)
                    .join(Group, UtilityTariff.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not tariff:
        return StatusErrorResponse(status="error", message="Тариф не знайдено")
    return StatusTariffResponse(
        status="ok",
        data=UtilityTariffOut(
            id=tariff.id,
            name=tariff.name,
            description=tariff.description,
            utility_type_id=tariff.utility_type_id,
            rate=tariff.rate,
            currency=tariff.currency,
            valid_from=tariff.valid_from.isoformat() if tariff.valid_from else None,
            valid_to=tariff.valid_to.isoformat() if tariff.valid_to else None,
            user_id=tariff.user_id,
            group_id=tariff.group_id,
            tariff_type=tariff.tariff_type,
            created=tariff.created.isoformat(),
            updated=tariff.updated.isoformat() if tariff.updated else None
        )
    )

@router.put("/api/utilities/tariffs/<int:tariff_id>", response_model=StatusTariffResponse, responses={400: {"model": StatusErrorResponse}, 404: {"model": StatusErrorResponse}})
async def update_utility_tariff(tariff_id, body: UtilityTariffData, user_id: str = Depends(get_current_user)):
    tariff = UtilityTariff.query.filter(
        and_(
            UtilityTariff.id == tariff_id,
            or_(
                UtilityTariff.user_id == user_id,
                UtilityTariff.id.in_(
                    db.session.query(UtilityTariff.id)
                    .join(Group, UtilityTariff.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not tariff:
        return StatusErrorResponse(status="error", message="Тариф не знайдено")
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    utility_type = SprUtilityType.query.filter(
        and_(
            SprUtilityType.id == body.utility_type_id,
            or_(
                SprUtilityType.user_id == user_id,
                SprUtilityType.id.in_(
                    db.session.query(SprUtilityType.id)
                    .join(Group, SprUtilityType.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not utility_type:
        return StatusErrorResponse(status="error", message="Тип комунальної послуги не знайдено")
    try:
        tariff.name = body.name
        tariff.description = body.description
        tariff.utility_type_id = body.utility_type_id
        tariff.rate = body.rate
        tariff.currency = body.currency
        tariff.valid_from = body.valid_from
        tariff.valid_to = body.valid_to
        tariff.user_id = body.user_id
        tariff.group_id = body.group_id
        tariff.tariff_type = body.tariff_type
        db.session.commit()
        return StatusTariffResponse(
            status="ok",
            data=UtilityTariffOut(
                id=tariff.id,
                name=tariff.name,
                description=tariff.description,
                utility_type_id=tariff.utility_type_id,
                rate=tariff.rate,
                currency=tariff.currency,
                valid_from=tariff.valid_from.isoformat() if tariff.valid_from else None,
                valid_to=tariff.valid_to.isoformat() if tariff.valid_to else None,
                user_id=tariff.user_id,
                group_id=tariff.group_id,
                tariff_type=tariff.tariff_type,
                created=tariff.created.isoformat(),
                updated=tariff.updated.isoformat() if tariff.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

@router.delete("/api/utilities/tariffs/{tariff_id}", response_model=StatusOkResponse, responses={400: {"model": StatusErrorResponse}, 404: {"model": StatusErrorResponse}})
async def delete_utility_tariff(tariff_id, user_id: str = Depends(get_current_user)):
    tariff = UtilityTariff.query.filter(
        and_(
            UtilityTariff.id == tariff_id,
            or_(
                UtilityTariff.user_id == user_id,
                UtilityTariff.id.in_(
                    db.session.query(UtilityTariff.id)
                    .join(Group, UtilityTariff.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not tariff:
        return StatusErrorResponse(status="error", message="Тариф не знайдено")
    try:
        readings = UtilityMeterReading.query.filter_by(tariff_id=tariff_id).count()
        if readings > 0:
            return StatusErrorResponse(status="error", message="Неможливо видалити тариф, для якого існують показники")
        db.session.delete(tariff)
        db.session.commit()
        return StatusOkResponse(status="ok")
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

# API для показників лічильників
@router.get("/api/utilities/readings", response_model=StatusReadingListResponse)
def get_utility_readings(user_id: str = Depends(get_current_user)):
    meter_id = request.args.get("meter_id")
    year = request.args.get("year")
    month = request.args.get("month")
    limit = request.args.get("limit", "12")
    query = get_user_resources(user_id, UtilityMeterReading)
    if meter_id:
        query = query.filter(UtilityMeterReading.meter_id == meter_id)
    if year:
        query = query.filter(UtilityMeterReading.year == year)
    if month:
        query = query.filter(UtilityMeterReading.month == month)
    try:
        limit_value = int(limit)
    except ValueError:
        limit_value = 12
    readings = query.order_by(UtilityMeterReading.year.desc(), UtilityMeterReading.month.desc()).limit(limit_value).all()
    result = [
        UtilityMeterReadingOut(
            id=reading.id,
            meter_id=reading.meter_id,
            reading_date=reading.reading_date.isoformat() if reading.reading_date else None,
            reading_value=reading.reading_value,
            previous_reading_id=reading.previous_reading_id,
            consumption=reading.consumption,
            user_id=reading.user_id,
            group_id=reading.group_id,
            tariff_id=reading.tariff_id,
            image_url=reading.image_url,
            month=reading.month,
            year=reading.year,
            cost=reading.cost,
            created=reading.created.isoformat() if reading.created else None,
            updated=reading.updated.isoformat() if reading.updated else None
        ) for reading in readings
    ]
    return StatusReadingListResponse(status="ok", data=result)

@router.post("/api/utilities/readings", response_model=StatusReadingResponse, responses={400: {"model": StatusErrorResponse}, 404: {"model": StatusErrorResponse}})
def create_utility_reading(body: UtilityMeterReadingData, user_id: str = Depends(get_current_user)):
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    meter = UtilityMeter.query.filter(
        and_(
            UtilityMeter.id == body.meter_id,
            or_(
                UtilityMeter.user_id == user_id,
                UtilityMeter.id.in_(
                    db.session.query(UtilityMeter.id)
                    .join(Group, UtilityMeter.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not meter:
        return StatusErrorResponse(status="error", message="Лічильник не знайдено")
    if body.tariff_id:
        tariff = UtilityTariff.query.filter(
            and_(
                UtilityTariff.id == body.tariff_id,
                or_(
                    UtilityTariff.user_id == user_id,
                    UtilityTariff.id.in_(
                        db.session.query(UtilityTariff.id)
                        .join(Group, UtilityTariff.group_id == Group.id)
                        .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                        .filter(UserGroupAssociation.user_id == user_id)
                    )
                )
            )
        ).first()
        if not tariff:
            return StatusErrorResponse(status="error", message="Тариф не знайдено")
    if not body.group_id and not body.user_id:
        body.user_id = user_id
    if not body.reading_date:
        body.reading_date = datetime.datetime.now(datetime.timezone.utc)
    try:
        existing_reading = UtilityMeterReading.query.filter(
            and_(
                UtilityMeterReading.meter_id == body.meter_id,
                UtilityMeterReading.month == body.month,
                UtilityMeterReading.year == body.year
            )
        ).first()
        if existing_reading:
            return StatusErrorResponse(status="error", message=f"Показник для цього лічильника за {body.month}/{body.year} вже існує")
        previous_reading = UtilityMeterReading.query.filter(
            UtilityMeterReading.meter_id == body.meter_id
        ).order_by(
            UtilityMeterReading.year.desc(),
            UtilityMeterReading.month.desc()
        ).first()
        if previous_reading:
            body.previous_reading_id = previous_reading.id
            body.consumption = body.reading_value - previous_reading.reading_value
            if body.tariff_id and (body.consumption is not None) and body.consumption > 0:
                tariff = UtilityTariff.query.get(body.tariff_id)
                if tariff:
                    body.cost = body.consumption * tariff.rate
        reading = UtilityMeterReading(**body.dict())
        db.session.add(reading)
        db.session.commit()
        return StatusReadingResponse(
            status="ok",
            data=UtilityMeterReadingOut(
                id=reading.id,
                meter_id=reading.meter_id,
                reading_date=reading.reading_date.isoformat() if reading.reading_date else None,
                reading_value=reading.reading_value,
                previous_reading_id=reading.previous_reading_id,
                consumption=reading.consumption,
                user_id=reading.user_id,
                group_id=reading.group_id,
                tariff_id=reading.tariff_id,
                image_url=reading.image_url,
                month=reading.month,
                year=reading.year,
                cost=reading.cost,
                created=reading.created.isoformat(),
                updated=reading.updated.isoformat() if reading.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

@router.get("/api/utilities/readings/{reading_id}", response_model=StatusReadingResponse, responses={404: {"model": StatusErrorResponse}})
def get_utility_reading(reading_id, user_id: str = Depends(get_current_user)):
    reading = UtilityMeterReading.query.filter(
        and_(
            UtilityMeterReading.id == reading_id,
            or_(
                UtilityMeterReading.user_id == user_id,
                UtilityMeterReading.id.in_(
                    db.session.query(UtilityMeterReading.id)
                    .join(Group, UtilityMeterReading.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not reading:
        return StatusErrorResponse(status="error", message="Показник не знайдено")
    return StatusReadingResponse(
        status="ok",
        data=UtilityMeterReadingOut(
            id=reading.id,
            meter_id=reading.meter_id,
            reading_date=reading.reading_date.isoformat() if reading.reading_date else None,
            reading_value=reading.reading_value,
            previous_reading_id=reading.previous_reading_id,
            consumption=reading.consumption,
            user_id=reading.user_id,
            group_id=reading.group_id,
            tariff_id=reading.tariff_id,
            image_url=reading.image_url,
            month=reading.month,
            year=reading.year,
            cost=reading.cost,
            created=reading.created.isoformat(),
            updated=reading.updated.isoformat() if reading.updated else None
        )
    )

@router.patch("/api/utilities/readings/{reading_id}", response_model=StatusReadingResponse, responses={400: {"model": StatusErrorResponse}, 404: {"model": StatusErrorResponse}})
def update_utility_reading(reading_id, body: UtilityMeterReadingData, user_id: str = Depends(get_current_user)):
    reading = UtilityMeterReading.query.filter(
        and_(
            UtilityMeterReading.id == reading_id,
            or_(
                UtilityMeterReading.user_id == user_id,
                UtilityMeterReading.id.in_(
                    db.session.query(UtilityMeterReading.id)
                    .join(Group, UtilityMeterReading.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not reading:
        return StatusErrorResponse(status="error", message="Показник не знайдено")
    if body.group_id and not check_group_access(user_id, body.group_id):
        raise HTTPException(403, "Немає доступу до цієї групи")
    meter = UtilityMeter.query.filter(
        and_(
            UtilityMeter.id == body.meter_id,
            or_(
                UtilityMeter.user_id == user_id,
                UtilityMeter.id.in_(
                    db.session.query(UtilityMeter.id)
                    .join(Group, UtilityMeter.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not meter:
        return StatusErrorResponse(status="error", message="Лічильник не знайдено")
    if body.tariff_id:
        tariff = UtilityTariff.query.filter(
            and_(
                UtilityTariff.id == body.tariff_id,
                or_(
                    UtilityTariff.user_id == user_id,
                    UtilityTariff.id.in_(
                        db.session.query(UtilityTariff.id)
                        .join(Group, UtilityTariff.group_id == Group.id)
                        .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                        .filter(UserGroupAssociation.user_id == user_id)
                    )
                )
            )
        ).first()
        if not tariff:
            return StatusErrorResponse(status="error", message="Тариф не знайдено")
    try:
        if reading.month != body.month or reading.year != body.year:
            existing_reading = UtilityMeterReading.query.filter(
                and_(
                    UtilityMeterReading.meter_id == body.meter_id,
                    UtilityMeterReading.month == body.month,
                    UtilityMeterReading.year == body.year,
                    UtilityMeterReading.id != reading_id
                )
            ).first()
            if existing_reading:
                return StatusErrorResponse(status="error", message=f"Показник для цього лічильника за {body.month}/{body.year} вже існує")
        reading.meter_id = body.meter_id
        reading.reading_date = body.reading_date
        reading.reading_value = body.reading_value
        reading.previous_reading_id = body.previous_reading_id
        reading.user_id = body.user_id
        reading.group_id = body.group_id
        reading.tariff_id = body.tariff_id
        reading.image_url = body.image_url
        reading.month = body.month
        reading.year = body.year
        if reading.previous_reading_id:
            previous_reading = UtilityMeterReading.query.get(reading.previous_reading_id)
            if previous_reading:
                reading.consumption = reading.reading_value - previous_reading.reading_value
        else:
            reading.consumption = body.consumption
        if reading.tariff_id and (reading.consumption is not None) and reading.consumption > 0:
            tariff = UtilityTariff.query.get(reading.tariff_id)
            if tariff:
                reading.cost = reading.consumption * tariff.rate
        else:
            reading.cost = body.cost
        db.session.commit()
        return StatusReadingResponse(
            status="ok",
            data=UtilityMeterReadingOut(
                id=reading.id,
                meter_id=reading.meter_id,
                reading_date=reading.reading_date.isoformat() if reading.reading_date else None,
                reading_value=reading.reading_value,
                previous_reading_id=reading.previous_reading_id,
                consumption=reading.consumption,
                user_id=reading.user_id,
                group_id=reading.group_id,
                tariff_id=reading.tariff_id,
                image_url=reading.image_url,
                month=reading.month,
                year=reading.year,
                cost=reading.cost,
                created=reading.created.isoformat(),
                updated=reading.updated.isoformat() if reading.updated else None
            )
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

@router.delete("/api/utilities/readings/{reading_id}", response_model=StatusOkResponse, responses={400: {"model": StatusErrorResponse}, 404: {"model": StatusErrorResponse}})
def delete_utility_reading(reading_id, user_id: str = Depends(get_current_user)):
    reading = UtilityMeterReading.query.filter(
        and_(
            UtilityMeterReading.id == reading_id,
            or_(
                UtilityMeterReading.user_id == user_id,
                UtilityMeterReading.id.in_(
                    db.session.query(UtilityMeterReading.id)
                    .join(Group, UtilityMeterReading.group_id == Group.id)
                    .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                    .filter(UserGroupAssociation.user_id == user_id)
                )
            )
        )
    ).first()
    if not reading:
        return StatusErrorResponse(status="error", message="Показник не знайдено")
    try:
        dependent_readings = UtilityMeterReading.query.filter_by(previous_reading_id=reading_id).count()
        if dependent_readings > 0:
            return StatusErrorResponse(status="error", message="Неможливо видалити показник, на який посилаються інші показники")
        db.session.delete(reading)
        db.session.commit()
        return StatusOkResponse(status="ok")
    except SQLAlchemyError as e:
        db.session.rollback()
        return StatusErrorResponse(status="error", message=str(e))

# API для статистики
@router.get("/api/utilities/statistics")
async def get_utility_statistics(user_id: str = Depends(get_current_user)):
    current_user = user_id
    user_id = current_user.get('user_id')
    
    meter_id = request.args.get("meter_id")
    utility_type_id = request.args.get("utility_type_id")
    year = request.args.get("year")
    
    if not meter_id and not utility_type_id:
        return {"status": "error", "message": "Потрібно вказати meter_id або utility_type_id"}, 400
    
    if meter_id:
        # Статистика для конкретного лічильника
        meter = UtilityMeter.query.filter(
            and_(
                UtilityMeter.id == meter_id,
                or_(
                    UtilityMeter.user_id == user_id,
                    UtilityMeter.id.in_(
                        db.session.query(UtilityMeter.id)
                        .join(Group, UtilityMeter.group_id == Group.id)
                        .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                        .filter(UserGroupAssociation.user_id == user_id)
                    )
                )
            )
        ).first()
        
        if not meter:
            return {"status": "error", "message": "Лічильник не знайдено"}, 404
        
        query = UtilityMeterReading.query.filter(UtilityMeterReading.meter_id == meter_id)
        
    else:
        # Статистика для всіх лічильників певного типу
        utility_type = SprUtilityType.query.filter(
            and_(
                SprUtilityType.id == utility_type_id,
                or_(
                    SprUtilityType.user_id == user_id,
                    SprUtilityType.id.in_(
                        db.session.query(SprUtilityType.id)
                        .join(Group, SprUtilityType.group_id == Group.id)
                        .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                        .filter(UserGroupAssociation.user_id == user_id)
                    )
                )
            )
        ).first()
        
        if not utility_type:
            return {"status": "error", "message": "Тип комунальної послуги не знайдено"}, 404
        
        # Отримуємо всі лічильники даного типу, які належать користувачу або його групам
        meters = UtilityMeter.query.filter(
            and_(
                UtilityMeter.utility_type_id == utility_type_id,
                or_(
                    UtilityMeter.user_id == user_id,
                    UtilityMeter.id.in_(
                        db.session.query(UtilityMeter.id)
                        .join(Group, UtilityMeter.group_id == Group.id)
                        .join(UserGroupAssociation, Group.id == UserGroupAssociation.group_id)
                        .filter(UserGroupAssociation.user_id == user_id)
                    )
                )
            )
        ).all()
        
        meter_ids = [meter.id for meter in meters]
        
        if not meter_ids:
            return {"status": "ok", "data": []}, 200
        
        query = UtilityMeterReading.query.filter(UtilityMeterReading.meter_id.in_(meter_ids))
    
    if year:
        query = query.filter(UtilityMeterReading.year == year)
    
    # Отримуємо показники, згруповані за місяцем та роком
    if meter_id:
        # Для одного лічильника - просто вибираємо показники
        readings = query.order_by(UtilityMeterReading.year.asc(), UtilityMeterReading.month.asc()).all()
        
        result = []
        for reading in readings:
            result.append({
                "month": reading.month,
                "year": reading.year,
                "reading_value": reading.reading_value,
                "consumption": reading.consumption,
                "cost": reading.cost
            })
    else:
        # Для всіх лічильників - групуємо по місяцю та року
        readings = db.session.query(
            UtilityMeterReading.year,
            UtilityMeterReading.month,
            func.sum(UtilityMeterReading.consumption).label('total_consumption'),
            func.sum(UtilityMeterReading.cost).label('total_cost')
        ).filter(
            UtilityMeterReading.meter_id.in_(meter_ids)
        )
        
        if year:
            readings = readings.filter(UtilityMeterReading.year == year)
        
        readings = readings.group_by(
            UtilityMeterReading.year,
            UtilityMeterReading.month
        ).order_by(
            UtilityMeterReading.year.asc(),
            UtilityMeterReading.month.asc()
        ).all()
        
        result = []
        for reading in readings:
            result.append({
                "month": reading.month,
                "year": reading.year,
                "total_consumption": float(reading.total_consumption) if reading.total_consumption else 0,
                "total_cost": float(reading.total_cost) if reading.total_cost else 0
            })
    
    return {"status": "ok", "data": result}