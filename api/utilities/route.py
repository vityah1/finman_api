from fastapi import APIRouter, Depends, Body, Query, HTTPException
from typing import List, Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from api.utilities.services import (
    get_utility_addresses, get_utility_address, create_utility_address,
    update_utility_address, delete_utility_address,
    get_utility_services, get_utility_service, create_utility_service, 
    update_utility_service, delete_utility_service,
    get_utility_tariffs, get_utility_tariff, create_utility_tariff, 
    update_utility_tariff, delete_utility_tariff,
    get_utility_readings, get_utility_reading, create_utility_reading, 
    update_utility_reading, delete_utility_reading
)
from api.utilities.calculation_service import UtilityCalculationService
from api.schemas.common import (
    UtilityAddressCreate, UtilityAddressUpdate, UtilityAddressResponse,
    UtilityServiceCreate, UtilityServiceUpdate, UtilityServiceResponse,
    UtilityTariffCreate, UtilityTariffUpdate, UtilityTariffResponse,
    UtilityReadingCreate, UtilityReadingUpdate, UtilityReadingResponse,
    GroupedReadingsResponse, LatestPeriodResponse
)
from dependencies import get_current_user
from models.models import User
import logging

router = APIRouter(tags=["utilities"])

logger = logging.getLogger(__name__)


# Utility Addresses routes
@router.get("/api/utilities/addresses")
async def get_addresses(current_user: User = Depends(get_current_user)):
    """Отримати всі адреси користувача"""
    return get_utility_addresses(current_user.id)


@router.get("/api/utilities/addresses/{address_id}")
async def get_address(
    address_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Отримати адресу за ID"""
    return get_utility_address(current_user.id, address_id)


@router.post("/api/utilities/addresses")
async def create_address(
    address: UtilityAddressCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Створити нову адресу"""
    return create_utility_address(current_user.id, address.model_dump())


@router.patch("/api/utilities/addresses/{address_id}")
async def update_address(
    address_id: int,
    address: UtilityAddressUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Оновити адресу"""
    return update_utility_address(current_user.id, address_id, address.model_dump(exclude_unset=True))


@router.delete("/api/utilities/addresses/{address_id}")
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user)
):
    """Видалити адресу"""
    return delete_utility_address(current_user.id, address_id)



# Utility Services routes
@router.get("/api/utilities/services")
async def get_services(
    address_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Отримати всі комунальні служби користувача"""
    return get_utility_services(current_user.id, address_id)


@router.get("/api/utilities/services/{service_id}")
async def get_service(
    service_id: int, 
    current_user: User = Depends(get_current_user)
):
    """Отримати комунальну службу за ID"""
    return get_utility_service(current_user.id, service_id)


@router.post("/api/utilities/services")
async def create_service(
    service: UtilityServiceCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Створити нову комунальну службу"""
    return create_utility_service(current_user.id, service.model_dump())


@router.patch("/api/utilities/services/{service_id}")
async def update_service(
    service_id: int,
    service: UtilityServiceUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Оновити комунальну службу"""
    return update_utility_service(current_user.id, service_id, service.model_dump(exclude_unset=True))


@router.delete("/api/utilities/services/{service_id}")
async def delete_service(
    service_id: int,
    current_user: User = Depends(get_current_user)
):
    """Видалити комунальну службу"""
    return delete_utility_service(current_user.id, service_id)


# Utility Tariffs routes
@router.get("/api/utilities/tariffs")
async def get_tariffs(
    service_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Отримати тарифи для комунальних служб"""
    return get_utility_tariffs(current_user.id, service_id)


@router.get("/api/utilities/tariffs/{tariff_id}")
async def get_tariff(
    tariff_id: int,
    current_user: User = Depends(get_current_user)
):
    """Отримати тариф за ID"""
    return get_utility_tariff(current_user.id, tariff_id)


@router.post("/api/utilities/tariffs", response_model=UtilityTariffResponse)
async def create_tariff(
    tariff: UtilityTariffCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Створити новий тариф"""
    return create_utility_tariff(current_user.id, tariff.model_dump())


@router.patch("/api/utilities/tariffs/{tariff_id}", response_model=UtilityTariffResponse)
async def update_tariff(
    tariff_id: int,
    tariff: UtilityTariffUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Оновити тариф"""
    return update_utility_tariff(current_user.id, tariff_id, tariff.model_dump(exclude_unset=True))


@router.delete("/api/utilities/tariffs/{tariff_id}")
async def delete_tariff(
    tariff_id: int,
    current_user: User = Depends(get_current_user)
):
    """Видалити тариф"""
    return delete_utility_tariff(current_user.id, tariff_id)


# Utility Tariffs routes
@router.get("/api/utilities/readings")
async def get_readings(
    address_id: Optional[int] = Query(None),
    service_id: Optional[int] = Query(None),
    period: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Отримати показники комунальних служб"""
    return get_utility_readings(current_user.id, address_id, service_id, period)


@router.get("/api/utilities/readings/{reading_id}")
async def get_reading(
    reading_id: int,
    current_user: User = Depends(get_current_user)
):
    """Отримати показник за ID"""
    return get_utility_reading(current_user.id, reading_id)


@router.post("/api/utilities/readings")
async def create_reading(
    reading: UtilityReadingCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Створити новий показник"""
    return create_utility_reading(current_user.id, reading.model_dump())


@router.patch("/api/utilities/readings/{reading_id}", response_model=UtilityReadingResponse)
async def update_reading(
    reading_id: int,
    reading: UtilityReadingUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Оновити показник"""
    logger.info(f"DEBUG: PATCH endpoint called for reading_id={reading_id}, data={reading.model_dump(exclude_unset=True)}")
    result = update_utility_reading(current_user.id, reading_id, reading.model_dump(exclude_unset=True))
    logger.info(f"DEBUG: PATCH endpoint completed successfully")
    return result


@router.delete("/api/utilities/readings/{reading_id}")
async def delete_reading(
    reading_id: int,
    current_user: User = Depends(get_current_user)
):
    """Видалити показник"""
    return delete_utility_reading(current_user.id, reading_id)


# Нові endpoints для розширених функцій
@router.get("/api/utilities/tariffs/grouped/{service_id}")
async def get_grouped_tariffs(
    service_id: int,
    period: str = Query(..., description="Період у форматі YYYY-MM"),
    current_user: User = Depends(get_current_user)
):
    """Отримати згруповані тарифи для служби на заданий період"""
    grouped_tariffs = UtilityCalculationService.get_grouped_tariffs(service_id, period)
    
    # Конвертуємо в список для JSON відповіді
    result = {}
    for group_code, tariffs in grouped_tariffs.items():
        result[group_code] = [
            {
                'id': t.id,
                'name': t.name,
                'rate': t.rate,
                # 'subscription_fee': t.subscription_fee,  # Поле видалено
                'tariff_type': t.tariff_type,
                'calculation_method': t.calculation_method,
                'percentage_of': t.percentage_of
            }
            for t in tariffs
        ]
    
    return result


@router.post("/api/utilities/readings/batch")
async def create_batch_readings(
    readings_data: Dict = Body(..., description="Дані для групового створення показників"),
    current_user: User = Depends(get_current_user)
):
    """Створити декілька показників одночасно (для електрики день/ніч)"""
    created_readings = []
    
    # Базові дані спільні для всіх показників
    base_data = {
        'address_id': readings_data['address_id'],
        'service_id': readings_data['service_id'],
        'period': readings_data['period'],
        'reading_date': readings_data.get('reading_date'),
        'is_paid': readings_data.get('is_paid', False),
        'notes': readings_data.get('notes')
    }
    
    # Створюємо показники для кожного типу
    for reading in readings_data.get('readings', []):
        reading_data = {**base_data}
        reading_data.update({
            'current_reading': reading['current_reading'],
            'previous_reading': reading.get('previous_reading'),
            'tariff_id': reading['tariff_id'],
            'reading_type': reading.get('reading_type', 'standard')
        })
        
        try:
            created = create_utility_reading(current_user.id, reading_data)
            created_readings.append(created)
        except Exception as e:
            # Якщо один показник не створився, відкочуємо всі
            for created_reading in created_readings:
                delete_utility_reading(current_user.id, created_reading['id'])
            raise HTTPException(400, f"Error creating batch readings: {str(e)}")
    
    return {
        'created_count': len(created_readings),
        'readings': created_readings
    }


@router.get("/api/utilities/readings/detailed/{service_id}")
async def get_detailed_readings(
    service_id: int,
    period: str = Query(..., description="Період у форматі YYYY-MM"),
    current_user: User = Depends(get_current_user)
):
    """Отримати показники з деталізованими розрахунками"""
    readings = get_utility_readings(
        user_id=current_user.id,
        service_id=service_id,
        period=period
    )
    
    # Додаємо розшифровку розрахунків
    import json
    for reading in readings:
        if reading.get('calculation_details'):
            try:
                reading['calculation_breakdown'] = json.loads(reading['calculation_details'])
            except:
                reading['calculation_breakdown'] = None
    
    return readings



@router.get("/api/utilities/readings/latest-period/{address_id}", response_model=LatestPeriodResponse)
async def get_latest_period_with_readings_endpoint(
    address_id: int,
    current_user: User = Depends(get_current_user)
):
    """Отримати останній період з показниками для адреси"""
    from api.utilities.services import get_latest_period_with_readings
    
    period = get_latest_period_with_readings(current_user.id, address_id)
    return {"period": period or datetime.now().strftime("%Y-%m")}


@router.get("/api/utilities/grouped-readings", response_model=GroupedReadingsResponse)
async def get_grouped_readings_endpoint(
    address_id: int = Query(..., description="ID адреси"),
    period: str = Query(None, description="Період у форматі YYYY-MM"),
    service_id: int = Query(None, description="ID служби для фільтрації"),
    current_user: User = Depends(get_current_user)
):
    """Отримати згруповані показники для адреси за період"""
    from api.utilities.services import get_grouped_readings, get_latest_period_with_readings
    
    # Якщо період не вказано, отримуємо останній період з показниками
    if not period:
        period = get_latest_period_with_readings(current_user.id, address_id)
        if not period:
            # Якщо немає показників взагалі, повертаємо поточний місяць
            period = datetime.now().strftime("%Y-%m")
    
    logger.info(f"Getting grouped readings for address {address_id}, period {period}, service_id {service_id}")
    result = get_grouped_readings(current_user.id, address_id, period, service_id)
    return result

