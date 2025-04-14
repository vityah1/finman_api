import logging
import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm.session import Session

from models import (
    SprUtilityType, UtilityMeter, UtilityTariff, UtilityMeterReading,
    User, Group, UserGroupAssociation
)
from mydb import db

logger = logging.getLogger()


def get_active_tariff(
    utility_type_id: int,
    tariff_type: str,
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    date: Optional[datetime.datetime] = None
) -> Optional[UtilityTariff]:
    """
    Отримати активний тариф для вказаного типу комунальної послуги та типу тарифу
    на вказану дату (або поточну, якщо дата не вказана)
    """
    if not date:
        date = datetime.datetime.now(datetime.timezone.utc)
    
    query = UtilityTariff.query.filter(
        and_(
            UtilityTariff.utility_type_id == utility_type_id,
            UtilityTariff.tariff_type == tariff_type,
            or_(
                UtilityTariff.valid_to.is_(None),
                UtilityTariff.valid_to > date
            ),
            UtilityTariff.valid_from <= date
        )
    )
    
    if user_id:
        query = query.filter(UtilityTariff.user_id == user_id)
    elif group_id:
        query = query.filter(UtilityTariff.group_id == group_id)
    
    return query.order_by(UtilityTariff.valid_from.desc()).first()


def calculate_consumption(
    reading_value: float,
    previous_reading_value: float
) -> float:
    """
    Розрахувати споживання на основі поточного та попереднього показників
    """
    return max(0, reading_value - previous_reading_value)


def calculate_cost(
    consumption: float,
    tariff: UtilityTariff
) -> float:
    """
    Розрахувати вартість на основі споживання та тарифу
    """
    if not consumption or not tariff or not tariff.rate:
        return 0
    
    return consumption * tariff.rate


def get_monthly_statistics(
    user_id: int,
    year: Optional[int] = None,
    utility_type_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Отримати місячну статистику споживання для користувача
    """
    # Отримуємо ID груп, до яких належить користувач
    user_groups = UserGroupAssociation.query.filter(
        UserGroupAssociation.user_id == user_id
    ).with_entities(UserGroupAssociation.group_id).all()
    
    group_ids = [group.group_id for group in user_groups]
    
    # Базовий запит для лічильників користувача та його груп
    meter_query = UtilityMeter.query.filter(
        or_(
            UtilityMeter.user_id == user_id,
            and_(
                UtilityMeter.group_id.in_(group_ids),
                UtilityMeter.group_id.isnot(None)
            )
        )
    )
    
    if utility_type_id:
        meter_query = meter_query.filter(UtilityMeter.utility_type_id == utility_type_id)
    
    meter_ids = [meter.id for meter in meter_query.all()]
    
    if not meter_ids:
        return []
    
    # Запит для показників лічильників
    reading_query = db.session.query(
        UtilityMeterReading.year,
        UtilityMeterReading.month,
        func.sum(UtilityMeterReading.consumption).label('total_consumption'),
        func.sum(UtilityMeterReading.cost).label('total_cost'),
        func.count(UtilityMeterReading.id).label('reading_count')
    ).filter(
        UtilityMeterReading.meter_id.in_(meter_ids)
    )
    
    if year:
        reading_query = reading_query.filter(UtilityMeterReading.year == year)
    
    readings = reading_query.group_by(
        UtilityMeterReading.year,
        UtilityMeterReading.month
    ).order_by(
        UtilityMeterReading.year.desc(),
        UtilityMeterReading.month.desc()
    ).all()
    
    result = []
    for reading in readings:
        result.append({
            "year": reading.year,
            "month": reading.month,
            "total_consumption": float(reading.total_consumption) if reading.total_consumption else 0,
            "total_cost": float(reading.total_cost) if reading.total_cost else 0,
            "reading_count": reading.reading_count
        })
    
    return result


def get_utility_types_with_meters(user_id: int) -> List[Dict[str, Any]]:
    """
    Отримати список типів комунальних послуг з кількістю лічильників для користувача
    """
    # Отримуємо ID груп, до яких належить користувач
    user_groups = UserGroupAssociation.query.filter(
        UserGroupAssociation.user_id == user_id
    ).with_entities(UserGroupAssociation.group_id).all()
    
    group_ids = [group.group_id for group in user_groups]
    
    # Запит для типів комунальних послуг з кількістю лічильників
    utility_types = db.session.query(
        SprUtilityType,
        func.count(UtilityMeter.id).label('meter_count')
    ).outerjoin(
        UtilityMeter,
        and_(
            UtilityMeter.utility_type_id == SprUtilityType.id,
            or_(
                UtilityMeter.user_id == user_id,
                and_(
                    UtilityMeter.group_id.in_(group_ids),
                    UtilityMeter.group_id.isnot(None)
                )
            )
        )
    ).filter(
        or_(
            SprUtilityType.user_id == user_id,
            and_(
                SprUtilityType.group_id.in_(group_ids),
                SprUtilityType.group_id.isnot(None)
            )
        )
    ).group_by(
        SprUtilityType.id
    ).all()
    
    result = []
    for ut, meter_count in utility_types:
        result.append({
            "id": ut.id,
            "name": ut.name,
            "description": ut.description,
            "user_id": ut.user_id,
            "group_id": ut.group_id,
            "meter_count": meter_count
        })
    
    return result 