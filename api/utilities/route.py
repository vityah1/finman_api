from fastapi import APIRouter, Depends, Body, Query
from typing import List, Optional

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
from api.schemas.common import (
    UtilityAddressCreate, UtilityAddressUpdate,
    UtilityServiceCreate, UtilityServiceUpdate,
    UtilityTariffCreate, UtilityTariffUpdate,
    UtilityReadingCreate, UtilityReadingUpdate
)
from dependencies import get_current_user
from models.models import User

router = APIRouter(tags=["utilities"])


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


@router.post("/api/utilities/tariffs")
async def create_tariff(
    tariff: UtilityTariffCreate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Створити новий тариф"""
    return create_utility_tariff(current_user.id, tariff.model_dump())


@router.patch("/api/utilities/tariffs/{tariff_id}")
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


# Utility Readings routes
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


@router.patch("/api/utilities/readings/{reading_id}")
async def update_reading(
    reading_id: int,
    reading: UtilityReadingUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Оновити показник"""
    return update_utility_reading(current_user.id, reading_id, reading.model_dump(exclude_unset=True))


@router.delete("/api/utilities/readings/{reading_id}")
async def delete_reading(
    reading_id: int,
    current_user: User = Depends(get_current_user)
):
    """Видалити показник"""
    return delete_utility_reading(current_user.id, reading_id)
