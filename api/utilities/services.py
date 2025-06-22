import logging
import json
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy import and_, desc

from api.schemas.common import (
    UtilityAddressResponse, UtilityServiceResponse, UtilityTariffResponse, UtilityReadingResponse
)
from models.models import UtilityAddress, UtilityService, UtilityTariff, UtilityReading
from api.utilities.calculation_service import UtilityCalculationService
from mydb import db

logger = logging.getLogger()


# Utility Addresses
def get_utility_addresses(user_id: int) -> List[dict]:
    """Отримати всі адреси користувача"""
    addresses = db.session().query(UtilityAddress).filter_by(
        user_id=user_id, is_active=True
    ).order_by(UtilityAddress.name).all()
    
    return [UtilityAddressResponse.model_validate(address).model_dump() for address in addresses]


def get_utility_address(user_id: int, address_id: int) -> dict:
    """Отримати адресу за ID"""
    address = db.session().query(UtilityAddress).filter_by(
        id=address_id, user_id=user_id
    ).first()
    
    if not address:
        raise HTTPException(404, 'Utility address not found')
    
    return UtilityAddressResponse.model_validate(address).model_dump()


def create_utility_address(user_id: int, data: dict) -> dict:
    """Створити нову адресу"""
    data['user_id'] = user_id
    address = UtilityAddress(**data)
    
    try:
        db.session().add(address)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating utility address: {err}")
        raise HTTPException(400, 'Error creating utility address')
    
    return UtilityAddressResponse.model_validate(address).model_dump()


def update_utility_address(user_id: int, address_id: int, data: dict) -> dict:
    """Оновити адресу"""
    address = db.session().query(UtilityAddress).filter_by(
        id=address_id, user_id=user_id
    ).first()
    
    if not address:
        raise HTTPException(404, 'Utility address not found')
    
    # Видаляємо None значення з data
    filtered_data = {k: v for k, v in data.items() if v is not None}
    address.update(**filtered_data)
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error updating utility address: {err}")
        raise HTTPException(400, 'Error updating utility address')
    
    return UtilityAddressResponse.model_validate(address).model_dump()



# Utility Services
def get_utility_services(user_id: int) -> List[dict]:
    """Отримати всі комунальні служби користувача"""
    services = db.session().query(UtilityService).filter_by(
        user_id=user_id, is_active=True
    ).order_by(UtilityService.name).all()
    
    return [UtilityServiceResponse.model_validate(service).model_dump() for service in services]


def get_utility_service(user_id: int, service_id: int) -> dict:
    """Отримати комунальну службу за ID"""
    service = db.session().query(UtilityService).filter_by(
        id=service_id, user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    return UtilityServiceResponse.model_validate(service).model_dump()


def create_utility_service(user_id: int, data: dict) -> dict:
    """Створити нову комунальну службу"""
    data['user_id'] = user_id
    service = UtilityService(**data)
    
    try:
        db.session().add(service)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating utility service: {err}")
        raise HTTPException(400, 'Error creating utility service')
    
    return UtilityServiceResponse.model_validate(service).model_dump()


def update_utility_service(user_id: int, service_id: int, data: dict) -> dict:
    """Оновити комунальну службу"""
    service = db.session().query(UtilityService).filter_by(
        id=service_id, user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    # Видаляємо None значення з data
    filtered_data = {k: v for k, v in data.items() if v is not None}
    service.update(**filtered_data)
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error updating utility service: {err}")
        raise HTTPException(400, 'Error updating utility service')
    
    return UtilityServiceResponse.model_validate(service).model_dump()


def delete_utility_service(user_id: int, service_id: int) -> dict:
    """Видалити комунальну службу (м'яке видалення)"""
    service = db.session().query(UtilityService).filter_by(
        id=service_id, user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    service.is_active = False
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error deleting utility service: {err}")
        raise HTTPException(400, 'Error deleting utility service')
    
    return {"result": "ok"}


# Utility Tariffs
def get_utility_tariffs(user_id: int, service_id: Optional[int] = None) -> List[dict]:
    """Отримати тарифи для комунальних служб"""
    query = db.session().query(UtilityTariff).join(UtilityService).filter(
        UtilityService.user_id == user_id
    )
    
    if service_id:
        query = query.filter(UtilityTariff.service_id == service_id)
    
    tariffs = query.order_by(desc(UtilityTariff.valid_from)).all()
    
    return [UtilityTariffResponse.model_validate(tariff).model_dump() for tariff in tariffs]


def get_utility_tariff(user_id: int, tariff_id: int) -> dict:
    """Отримати тариф за ID"""
    tariff = db.session().query(UtilityTariff).join(UtilityService).filter(
        UtilityTariff.id == tariff_id,
        UtilityService.user_id == user_id
    ).first()
    
    if not tariff:
        raise HTTPException(404, 'Utility tariff not found')
    
    return UtilityTariffResponse.model_validate(tariff).model_dump()


def create_utility_tariff(user_id: int, data: dict) -> dict:
    """Створити новий тариф"""
    # Перевіряємо, що служба належить користувачу
    service = db.session().query(UtilityService).filter_by(
        id=data['service_id'], user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    tariff = UtilityTariff(**data)
    
    try:
        db.session().add(tariff)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating utility tariff: {err}")
        raise HTTPException(400, 'Error creating utility tariff')
    
    return UtilityTariffResponse.model_validate(tariff).model_dump()


def update_utility_tariff(user_id: int, tariff_id: int, data: dict) -> dict:
    """Оновити тариф"""
    tariff = db.session().query(UtilityTariff).join(UtilityService).filter(
        UtilityTariff.id == tariff_id,
        UtilityService.user_id == user_id
    ).first()
    
    if not tariff:
        raise HTTPException(404, 'Utility tariff not found')
    
    # Видаляємо None значення з data
    filtered_data = {k: v for k, v in data.items() if v is not None}
    tariff.update(**filtered_data)
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error updating utility tariff: {err}")
        raise HTTPException(400, 'Error updating utility tariff')
    
    return UtilityTariffResponse.model_validate(tariff).model_dump()


def delete_utility_tariff(user_id: int, tariff_id: int) -> dict:
    """Видалити тариф (м'яке видалення)"""
    tariff = db.session().query(UtilityTariff).join(UtilityService).filter(
        UtilityTariff.id == tariff_id,
        UtilityService.user_id == user_id
    ).first()
    
    if not tariff:
        raise HTTPException(404, 'Utility tariff not found')
    
    tariff.is_active = False
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error deleting utility tariff: {err}")
        raise HTTPException(400, 'Error deleting utility tariff')
    
    return {"result": "ok"}


def create_shared_meter_readings(user_id: int, service: UtilityService, data: dict) -> dict:
    """Створити показники для служби зі спільним лічильником"""
    # Отримуємо всі активні тарифи для періоду
    grouped_tariffs = UtilityCalculationService.get_grouped_tariffs(
        service.id, data['period']
    )
    
    # Якщо передано конкретний тариф, знаходимо його групу
    selected_tariff = db.session().query(UtilityTariff).get(data.get('tariff_id'))
    if not selected_tariff:
        raise HTTPException(400, 'Tariff not found for shared meter service')
    
    group_code = selected_tariff.group_code or 'default'
    group_tariffs = grouped_tariffs.get(group_code, [])
    
    if not group_tariffs:
        raise HTTPException(400, 'No tariffs found for the group')
    
    # Знаходимо попередній показник для конкретного тарифу
    if not data.get('previous_reading'):
        # Для служб з has_shared_meter шукаємо по службі
        if service.has_shared_meter:
            previous_reading = db.session().query(UtilityReading).filter(
                UtilityReading.user_id == user_id,
                UtilityReading.service_id == service.id,
                UtilityReading.period < data['period']
            ).order_by(desc(UtilityReading.period)).first()
        else:
            # Для звичайних служб шукаємо по тарифу
            previous_reading = db.session().query(UtilityReading).filter(
                UtilityReading.user_id == user_id,
                UtilityReading.service_id == service.id,
                UtilityReading.tariff_id == selected_tariff.id,
                UtilityReading.period < data['period']
            ).order_by(desc(UtilityReading.period)).first()
        
        if previous_reading:
            data['previous_reading'] = previous_reading.current_reading
        else:
            data['previous_reading'] = 0
    
    # Розраховуємо споживання
    consumption = data['current_reading'] - data['previous_reading']
    
    # Виконуємо розрахунок для всієї групи
    calculation_result = UtilityCalculationService.calculate_shared_meter_charges(
        consumption, group_tariffs
    )
    
    # Створюємо єдиний запис з повним розрахунком
    reading_data = {
        'user_id': user_id,
        'address_id': data['address_id'],
        'service_id': service.id,
        'period': data['period'],
        'current_reading': data['current_reading'],
        'previous_reading': data['previous_reading'],
        'consumption': consumption,
        'tariff_id': selected_tariff.id,  # Основний тариф
        'amount': calculation_result['total_amount'],
        'calculation_details': json.dumps(calculation_result, ensure_ascii=False),
        'reading_date': data.get('reading_date'),
        'is_paid': data.get('is_paid', False),
        'notes': data.get('notes'),
        'reading_type': 'shared'
    }
    
    reading = UtilityReading(**reading_data)
    
    try:
        db.session().add(reading)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating shared meter reading: {err}")
        raise HTTPException(400, f'Error creating shared meter reading: {str(err)}')
    
    return UtilityReadingResponse.model_validate(reading).model_dump()


def create_utility_reading(user_id: int, data: dict) -> dict:
    """Створити новий показник"""
    # Перевіряємо, що служба належить користувачу
    service = db.session().query(UtilityService).filter_by(
        id=data['service_id'], user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    # Перевіряємо, чи служба має спільний лічильник
    if service.has_shared_meter:
        # Для служб зі спільним лічильником створюємо показники для всіх активних тарифів групи
        return create_shared_meter_readings(user_id, service, data)
    
    # Стандартне створення для звичайних служб
    # Перевіряємо, що тариф існує та належить цій службі
    tariff = db.session().query(UtilityTariff).filter_by(
        id=data['tariff_id'], service_id=data['service_id']
    ).first()
    
    if not tariff:
        raise HTTPException(404, 'Utility tariff not found')
    
    data['user_id'] = user_id
    
    # Якщо не передано попередній показник, знаходимо його автоматично
    if not data.get('previous_reading'):
        previous_reading = db.session().query(UtilityReading).filter(
            UtilityReading.user_id == user_id,
            UtilityReading.service_id == data['service_id'],
            UtilityReading.tariff_id == data['tariff_id'],
            UtilityReading.period < data['period']
        ).order_by(desc(UtilityReading.period)).first()
        
        if previous_reading:
            data['previous_reading'] = previous_reading.current_reading
        else:
            data['previous_reading'] = 0
    
    # Розраховуємо споживання
    data['consumption'] = data['current_reading'] - data['previous_reading']
    
    # Використовуємо новий сервіс розрахунків
    grouped_tariffs = UtilityCalculationService.get_grouped_tariffs(
        service.id, data['period']
    )
    
    # Підготовка даних для розрахунку
    reading_data = {
        'current_reading': data['current_reading'],
        'previous_reading': data['previous_reading'],
        'tariff_id': data['tariff_id'],
        'reading_type': data.get('reading_type', 'standard')
    }
    
    # Якщо є група тарифів, додаємо її
    if tariff.group_code:
        reading_data['tariff_group'] = tariff.group_code
    
    # Виконуємо розрахунок
    calculation_result = UtilityCalculationService.calculate_reading_amount(
        service, reading_data, grouped_tariffs
    )
    
    # Зберігаємо результати
    data['amount'] = calculation_result['total_amount']
    data['calculation_details'] = json.dumps(calculation_result, ensure_ascii=False)
    
    reading = UtilityReading(**data)
    
    try:
        db.session().add(reading)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating utility reading: {err}")
        raise HTTPException(400, 'Error creating utility reading')
    
    return UtilityReadingResponse.model_validate(reading).model_dump()


def update_utility_reading(user_id: int, reading_id: int, data: dict) -> dict:
    """Оновити показник"""
    reading = db.session().query(UtilityReading).filter_by(
        id=reading_id, user_id=user_id
    ).first()
    
    if not reading:
        raise HTTPException(404, 'Utility reading not found')
    
    # Видаляємо None значення з data
    filtered_data = {k: v for k, v in data.items() if v is not None}
    
    # Якщо змінився поточний показник, перерахуємо споживання та суму
    if 'current_reading' in filtered_data:
        previous = filtered_data.get('previous_reading', reading.previous_reading)
        filtered_data['consumption'] = filtered_data['current_reading'] - previous
        
        # Отримуємо службу
        service = reading.service
        
        # Використовуємо новий сервіс розрахунків
        grouped_tariffs = UtilityCalculationService.get_grouped_tariffs(
            service.id, reading.period
        )
        
        # Якщо змінився тариф, використовуємо його, інакше поточний
        if 'tariff_id' in filtered_data:
            tariff = db.session().query(UtilityTariff).get(filtered_data['tariff_id'])
        else:
            tariff = reading.tariff
        
        # Підготовка даних для розрахунку
        reading_data = {
            'current_reading': filtered_data['current_reading'],
            'previous_reading': previous,
            'tariff_id': tariff.id if tariff else None,
            'reading_type': filtered_data.get('reading_type', reading.reading_type or 'standard')
        }
        
        # Якщо є група тарифів, додаємо її
        if tariff and tariff.group_code:
            reading_data['tariff_group'] = tariff.group_code
        
        # Виконуємо розрахунок
        calculation_result = UtilityCalculationService.calculate_reading_amount(
            service, reading_data, grouped_tariffs
        )
        
        # Зберігаємо результати
        filtered_data['amount'] = calculation_result['total_amount']
        filtered_data['calculation_details'] = json.dumps(calculation_result, ensure_ascii=False)
    
    reading.update(**filtered_data)
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error updating utility reading: {err}")
        raise HTTPException(400, 'Error updating utility reading')
    
    return UtilityReadingResponse.model_validate(reading).model_dump()


def delete_utility_reading(user_id: int, reading_id: int) -> dict:
    """Видалити показник"""
    reading = db.session().query(UtilityReading).filter_by(
        id=reading_id, user_id=user_id
    ).first()
    
    if not reading:
        raise HTTPException(404, 'Utility reading not found')
    
    try:
        # Перевіряємо, чи служба має спільний лічильник
        service = reading.service
        
        if service.has_shared_meter:
            # Для служб зі спільним лічільником видаляємо всі показники за той же період
            related_readings = db.session().query(UtilityReading).filter(
                UtilityReading.user_id == user_id,
                UtilityReading.service_id == reading.service_id,
                UtilityReading.period == reading.period
            ).all()
            
            for related_reading in related_readings:
                db.session().delete(related_reading)
                
            logger.info(f"Deleted {len(related_readings)} related readings for shared meter service {service.name}")
        else:
            # Стандартне видалення одного показника
            db.session().delete(reading)
        
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error deleting utility reading: {err}")
        raise HTTPException(400, 'Error deleting utility reading')
    
    return {"result": "ok"}


def delete_utility_address(user_id: int, address_id: int) -> dict:
    """Видалити адресу (м'яке видалення)"""
    address = db.session().query(UtilityAddress).filter_by(
        id=address_id, user_id=user_id
    ).first()
    
    if not address:
        raise HTTPException(404, 'Utility address not found')
    
    address.is_active = False
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error deleting utility address: {err}")
        raise HTTPException(400, 'Error deleting utility address')
    
    return {"result": "ok"}


# Utility Services
def get_utility_services(user_id: int, address_id: Optional[int] = None) -> List[dict]:
    """Отримати всі комунальні служби користувача"""
    query = db.session().query(UtilityService).filter_by(
        user_id=user_id, is_active=True
    )
    
    if address_id:
        query = query.filter(UtilityService.address_id == address_id)
    
    services = query.order_by(UtilityService.name).all()
    
    return [UtilityServiceResponse.model_validate(service).model_dump() for service in services]


def get_utility_service(user_id: int, service_id: int) -> dict:
    """Отримати комунальну службу за ID"""
    service = db.session().query(UtilityService).filter_by(
        id=service_id, user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    return UtilityServiceResponse.model_validate(service).model_dump()


def create_utility_service(user_id: int, data: dict) -> dict:
    """Створити нову комунальну службу"""
    # Перевіряємо, що адреса належить користувачу
    address = db.session().query(UtilityAddress).filter_by(
        id=data['address_id'], user_id=user_id
    ).first()
    
    if not address:
        raise HTTPException(404, 'Utility address not found')
    
    data['user_id'] = user_id
    service = UtilityService(**data)
    
    try:
        db.session().add(service)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating utility service: {err}")
        raise HTTPException(400, 'Error creating utility service')
    
    return UtilityServiceResponse.model_validate(service).model_dump()


def update_utility_service(user_id: int, service_id: int, data: dict) -> dict:
    """Оновити комунальну службу"""
    service = db.session().query(UtilityService).filter_by(
        id=service_id, user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    # Якщо змінюється адреса, перевіряємо її
    if 'address_id' in data:
        address = db.session().query(UtilityAddress).filter_by(
            id=data['address_id'], user_id=user_id
        ).first()
        
        if not address:
            raise HTTPException(404, 'Utility address not found')
    
    # Видаляємо None значення з data
    filtered_data = {k: v for k, v in data.items() if v is not None}
    service.update(**filtered_data)
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error updating utility service: {err}")
        raise HTTPException(400, 'Error updating utility service')
    
    return UtilityServiceResponse.model_validate(service).model_dump()


def delete_utility_service(user_id: int, service_id: int) -> dict:
    """Видалити комунальну службу (м'яке видалення)"""
    service = db.session().query(UtilityService).filter_by(
        id=service_id, user_id=user_id
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    service.is_active = False
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error deleting utility service: {err}")
        raise HTTPException(400, 'Error deleting utility service')
    
    return {"result": "ok"}


def create_utility_reading(user_id: int, data: dict) -> dict:
    """Створити новий показник"""
    # Перевіряємо, що адреса належить користувачу
    address = db.session().query(UtilityAddress).filter_by(
        id=data['address_id'], user_id=user_id
    ).first()
    
    if not address:
        raise HTTPException(404, 'Utility address not found')
    
    # Перевіряємо, що служба належить користувачу та адресі
    service = db.session().query(UtilityService).filter_by(
        id=data['service_id'], user_id=user_id, address_id=data['address_id']
    ).first()
    
    if not service:
        raise HTTPException(404, 'Utility service not found')
    
    # Перевіряємо, що тариф існує та належить цій службі
    tariff = db.session().query(UtilityTariff).filter_by(
        id=data['tariff_id'], service_id=data['service_id']
    ).first()
    
    if not tariff:
        raise HTTPException(404, 'Utility tariff not found')
    
    data['user_id'] = user_id
    
    # Якщо не передано попередній показник, знаходимо його автоматично
    if not data.get('previous_reading'):
        previous_reading = db.session().query(UtilityReading).filter(
            UtilityReading.user_id == user_id,
            UtilityReading.address_id == data['address_id'],
            UtilityReading.service_id == data['service_id'],
            UtilityReading.period < data['period']
        ).order_by(desc(UtilityReading.period)).first()
        
        if previous_reading:
            data['previous_reading'] = previous_reading.current_reading
        else:
            data['previous_reading'] = 0
    
    # Розраховуємо споживання
    data['consumption'] = data['current_reading'] - data['previous_reading']
    
    # Розраховуємо суму
    if data['consumption'] > 0:
        data['amount'] = (data['consumption'] * tariff.rate) + (tariff.subscription_fee or 0)
    else:
        # Навіть якщо споживання 0, може бути абонплата
        data['amount'] = tariff.subscription_fee or 0
    
    reading = UtilityReading(**data)
    
    try:
        db.session().add(reading)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error creating utility reading: {err}")
        raise HTTPException(400, 'Error creating utility reading')
    
    return UtilityReadingResponse.model_validate(reading).model_dump()


def get_utility_readings(user_id: int, address_id: Optional[int] = None, 
                        service_id: Optional[int] = None, period: Optional[str] = None) -> List[dict]:
    """Отримати показники комунальних служб"""
    query = db.session().query(UtilityReading).filter_by(user_id=user_id)
    
    if address_id:
        query = query.filter(UtilityReading.address_id == address_id)
    
    if service_id:
        query = query.filter(UtilityReading.service_id == service_id)
    
    if period:
        query = query.filter(UtilityReading.period == period)
    
    readings = query.order_by(desc(UtilityReading.period), 
                             desc(UtilityReading.reading_date)).all()
    
    return [UtilityReadingResponse.model_validate(reading).model_dump() for reading in readings]


def get_utility_reading(user_id: int, reading_id: int) -> dict:
    """Отримати показник за ID"""
    reading = db.session().query(UtilityReading).filter_by(
        id=reading_id, user_id=user_id
    ).first()
    
    if not reading:
        raise HTTPException(404, 'Utility reading not found')
    
    return UtilityReadingResponse.model_validate(reading).model_dump()


def update_utility_reading(user_id: int, reading_id: int, data: dict) -> dict:
    """Оновити показник"""
    reading = db.session().query(UtilityReading).filter_by(
        id=reading_id, user_id=user_id
    ).first()
    
    if not reading:
        raise HTTPException(404, 'Utility reading not found')
    
    # Видаляємо None значення з data
    filtered_data = {k: v for k, v in data.items() if v is not None}
    
    # Якщо змінився поточний показник, перерахуємо споживання та суму
    if 'current_reading' in filtered_data:
        previous = filtered_data.get('previous_reading', reading.previous_reading)
        filtered_data['consumption'] = filtered_data['current_reading'] - previous
        
        # Отримуємо службу
        service = reading.service
        
        # Використовуємо новий сервіс розрахунків
        grouped_tariffs = UtilityCalculationService.get_grouped_tariffs(
            service.id, reading.period
        )
        
        # Якщо змінився тариф, використовуємо його, інакше поточний
        if 'tariff_id' in filtered_data:
            tariff = db.session().query(UtilityTariff).get(filtered_data['tariff_id'])
        else:
            tariff = reading.tariff
        
        # Підготовка даних для розрахунку
        reading_data = {
            'current_reading': filtered_data['current_reading'],
            'previous_reading': previous,
            'tariff_id': tariff.id if tariff else None,
            'reading_type': filtered_data.get('reading_type', reading.reading_type or 'standard')
        }
        
        # Якщо є група тарифів, додаємо її
        if tariff and tariff.group_code:
            reading_data['tariff_group'] = tariff.group_code
        
        # Виконуємо розрахунок
        calculation_result = UtilityCalculationService.calculate_reading_amount(
            service, reading_data, grouped_tariffs
        )
        
        # Зберігаємо результати
        filtered_data['amount'] = calculation_result['total_amount']
        filtered_data['calculation_details'] = json.dumps(calculation_result, ensure_ascii=False)
    
    reading.update(**filtered_data)
    
    try:
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f"Error updating utility reading: {err}")
        raise HTTPException(400, 'Error updating utility reading')
    
    return UtilityReadingResponse.model_validate(reading).model_dump()



def get_latest_period_with_readings(user_id: int, address_id: int) -> Optional[str]:
    """Отримати останній період з показниками для адреси"""
    latest_reading = db.session().query(UtilityReading).join(
        UtilityService
    ).filter(
        UtilityService.user_id == user_id,
        UtilityService.address_id == address_id
    ).order_by(UtilityReading.period.desc()).first()
    
    return latest_reading.period if latest_reading else None


def get_grouped_readings(user_id: int, address_id: int, period: str) -> dict:
    """Отримати згруповані показники для адреси за період"""
    
    # Отримуємо всі показники для адреси за період
    readings = db.session().query(UtilityReading).join(
        UtilityService
    ).filter(
        UtilityService.user_id == user_id,
        UtilityService.address_id == address_id,
        UtilityReading.period == period
    ).all()
    
    # Отримуємо всі служби для групування
    services = db.session().query(UtilityService).filter(
        UtilityService.user_id == user_id,
        UtilityService.address_id == address_id,
        UtilityService.is_active == True
    ).all()
    
    # Групуємо показники за service_group або окремими службами
    grouped_data = {}
    service_groups = {}
    
    # Спочатку групуємо служби
    for service in services:
        if service.service_group:
            if service.service_group not in service_groups:
                service_groups[service.service_group] = {
                    'group_name': service.service_group,
                    'services': [],
                    'readings': [],
                    'total_amount': 0,
                    'has_shared_meter': False
                }
            # Конвертуємо service в словник
            service_dict = {
                'id': service.id,
                'name': service.name,
                'unit': service.unit,
                'has_shared_meter': service.has_shared_meter
            }
            service_groups[service.service_group]['services'].append(service_dict)
            if service.has_shared_meter:
                service_groups[service.service_group]['has_shared_meter'] = True
    
    # Обробляємо показники
    for reading in readings:
        service = reading.service
        tariff = reading.tariff
        
        if service.service_group and service.service_group in service_groups:
            # Додаємо до групи
            group = service_groups[service.service_group]
            reading_data = UtilityReadingResponse.model_validate(reading).model_dump()
            reading_data['service_name'] = service.name
            reading_data['tariff_name'] = tariff.name if tariff else None
            reading_data['tariff_type'] = tariff.tariff_type if tariff else None
            reading_data['tariff'] = {'rate': tariff.rate} if tariff else None
            group['readings'].append(reading_data)
            group['total_amount'] += reading.amount or 0
        else:
            # Окрема служба без групи
            service_key = f"service_{service.id}"
            if service_key not in grouped_data:
                grouped_data[service_key] = {
                    'service_id': service.id,
                    'service_name': service.name,
                    'unit': service.unit,
                    'has_shared_meter': service.has_shared_meter,
                    'readings': [],
                    'total_amount': 0
                }
            
            reading_data = UtilityReadingResponse.model_validate(reading).model_dump()
            reading_data['service_name'] = service.name
            reading_data['tariff_name'] = tariff.name if tariff else None
            reading_data['tariff'] = {'rate': tariff.rate} if tariff else None
            grouped_data[service_key]['readings'].append(reading_data)
            grouped_data[service_key]['total_amount'] += reading.amount or 0
    
    # Форматуємо результат
    result = {
        'address_id': address_id,
        'period': period,
        'service_groups': list(service_groups.values()),
        'services': list(grouped_data.values())
    }
    
    return result
