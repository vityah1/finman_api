#!/usr/bin/env python3
"""
Спільні функції для імпорту комунальних показників
"""

import pandas as pd
import logging
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from models.models import UtilityAddress, UtilityService, UtilityTariff, UtilityReading
from mydb import db

logger = logging.getLogger(__name__)


def parse_number(value):
    """Парсинг числа з рядка з підтримкою українського та американського форматування"""
    if pd.isna(value) or value == '' or value == 0:
        return 0
    
    # Конвертуємо в рядок якщо потрібно
    value = str(value).strip()
    
    # Зберігаємо знак
    is_negative = value.startswith('-')
    if is_negative:
        value = value[1:]
    
    # Видаляємо непотрібні символи (валюти, текст)
    value = re.sub(r'[^\d,.\s]', '', value)
    
    # Українське форматування: пробіли як роздільники тисяч, кома як десяткова
    if ' ' in value and ',' in value:
        # Наприклад: "1 268,50" -> "1268.50"
        value = value.replace(' ', '').replace(',', '.')
    # Американське форматування: коми як роздільники тисяч, крапка як десяткова  
    elif ',' in value and '.' in value:
        # Наприклад: "1,268.50" -> "1268.50"
        value = value.replace(',', '')
    # Тільки кома (десяткова)
    elif ',' in value:
        # Наприклад: "268,50" -> "268.50"
        value = value.replace(',', '.')
    # Видаляємо пробіли між цифрами (роздільники тисяч)
    elif ' ' in value:
        value = value.replace(' ', '')
    
    try:
        result = float(value)
        return -result if is_negative else result
    except:
        return 0


def create_or_get_address(user_id, address_name, address_full):
    """Створити або отримати адресу"""
    # Шукаємо по повній адресі
    address = db.session.query(UtilityAddress).filter_by(
        address=address_full,
        user_id=user_id
    ).first()
    
    if not address:
        # Якщо не знайшли, шукаємо по назві
        address = db.session.query(UtilityAddress).filter_by(
            name=address_name,
            user_id=user_id
        ).first()
    
    if not address:
        address = UtilityAddress(
            user_id=user_id,
            name=address_name,
            address=address_full
        )
        db.session.add(address)
        db.session.commit()
        logger.info(f"Створено адресу: {address_name}")
    else:
        logger.info(f"Знайдено існуючу адресу: {address_name} (ID: {address.id})")
    
    return address


def get_or_create_tariff(service_id, name, rate, currency, valid_from, valid_to, is_active, tariff_type, group_code, source):
    """Знайти існуючий тариф або створити новий"""
    existing_tariff = db.session.query(UtilityTariff).filter(
        UtilityTariff.service_id == service_id,
        UtilityTariff.name == name,
        UtilityTariff.valid_from == valid_from,
        UtilityTariff.tariff_type == tariff_type
    ).first()
    
    if existing_tariff:
        logger.info(f"Використовуємо існуючий тариф: {name} (ID: {existing_tariff.id})")
        existing_tariff.rate = rate
        existing_tariff.currency = currency
        existing_tariff.valid_to = valid_to
        existing_tariff.is_active = is_active
        existing_tariff.group_code = group_code
        existing_tariff.source = source
        return existing_tariff
    else:
        new_tariff = UtilityTariff(
            service_id=service_id,
            name=name,
            rate=rate,
            currency=currency,
            valid_from=valid_from,
            valid_to=valid_to,
            is_active=is_active,
            tariff_type=tariff_type,
            group_code=group_code,
            source=source
        )
        db.session.add(new_tariff)
        logger.info(f"Створено новий тариф: {name}")
        return new_tariff


def analyze_gas_subscription_fees(df, gas_subscription_column=9):
    """Аналізує зміни абонплати газу протягом часу з Excel файлу"""
    subscription_periods = []
    current_fee = None
    start_date = None
    
    for i in range(len(df)):
        if i < 5:  # Пропускаємо заголовки (перші 5 рядків)
            continue
            
        date_value = df.iloc[i, 0]  # Колонка 0 - дата
        if pd.isna(date_value):
            continue
            
        try:
            if isinstance(date_value, str):
                date = datetime.strptime(date_value, '%d.%m.%Y')
            else:
                date = date_value
            # Визначаємо період (віднімаємо місяць)
            period_date = date - relativedelta(months=1)
        except:
            continue
        
        # Абонплата газу в вказаній колонці
        fee_value = df.iloc[i, gas_subscription_column] if len(df.columns) > gas_subscription_column else None
        fee = parse_number(fee_value) if not pd.isna(fee_value) else 0
            
        if fee and fee != current_fee:
            # Завершуємо попередній період
            if current_fee is not None and start_date is not None:
                subscription_periods.append({
                    'fee': current_fee,
                    'from': start_date,
                    'to': period_date
                })
            # Починаємо новий період
            current_fee = fee
            start_date = period_date
    
    # Додаємо останній період
    if current_fee is not None and start_date is not None:
        subscription_periods.append({
            'fee': current_fee,
            'from': start_date,
            'to': None  # Діючий тариф
        })
    
    return subscription_periods


def clean_existing_data(address_name, user_id, preserve_may_2025=True):
    """Очищення існуючих даних із збереженням травня 2025"""
    address = db.session.query(UtilityAddress).filter_by(
        user_id=user_id, 
        name=address_name
    ).first()
    
    if address:
        # Знаходимо всі служби для цієї адреси
        services = db.session.query(UtilityService).filter_by(address_id=address.id).all()
        service_ids = [s.id for s in services]
        
        if service_ids:
            if preserve_may_2025:
                # КРОК 1: Знаходимо тарифи, які використовувались за травень 2025 (зберігаємо їх)
                may_2025_tariffs = db.session.query(UtilityTariff).join(UtilityReading).filter(
                    UtilityReading.period == '2025-05',
                    UtilityReading.user_id == user_id,
                    UtilityTariff.service_id.in_(service_ids)
                ).distinct().all()
                
                may_2025_tariff_ids = [t.id for t in may_2025_tariffs]
                logger.info(f"Знайдено тарифів за травень 2025 (зберігаємо): {len(may_2025_tariffs)} (IDs: {may_2025_tariff_ids})")
                
                # КРОК 2: Видаляємо ВСІ показники крім травня 2025
                deleted_readings = db.session.query(UtilityReading).filter(
                    UtilityReading.service_id.in_(service_ids),
                    UtilityReading.user_id == user_id,
                    UtilityReading.period != '2025-05'  # Зберігаємо тільки травень 2025
                ).delete(synchronize_session=False)
                db.session.commit()
                logger.info(f"Видалено {deleted_readings} показників (збережено травень 2025)")
                
                # КРОК 3: Видаляємо тарифи, крім тих що використовувались за травень 2025
                if may_2025_tariff_ids:
                    deleted_tariffs = db.session.query(UtilityTariff).filter(
                        UtilityTariff.service_id.in_(service_ids),
                        ~UtilityTariff.id.in_(may_2025_tariff_ids)
                    ).delete(synchronize_session=False)
                else:
                    deleted_tariffs = db.session.query(UtilityTariff).filter(
                        UtilityTariff.service_id.in_(service_ids)
                    ).delete(synchronize_session=False)
                
                db.session.commit()
                logger.info(f"Видалено {deleted_tariffs} тарифів (збережено тарифи за травень 2025: {len(may_2025_tariff_ids)})")
            else:
                # Видаляємо всі дані без збереження
                deleted_readings = db.session.query(UtilityReading).filter(
                    UtilityReading.service_id.in_(service_ids),
                    UtilityReading.user_id == user_id
                ).delete(synchronize_session=False)
                
                deleted_tariffs = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id.in_(service_ids)
                ).delete(synchronize_session=False)
                
                db.session.commit()
                logger.info(f"Видалено {deleted_readings} показників і {deleted_tariffs} тарифів")
        else:
            logger.info("Служби не знайдені для цієї адреси")
    else:
        logger.info("Адреса не знайдена, буде створена нова")


def calculate_previous_readings_and_amounts(address_id, preserve_amounts=False):
    """Розрахунок попередніх показників та сум"""
    logger.info("Розрахунок попередніх показників та сум...")
    
    readings = db.session.query(UtilityReading).filter_by(
        address_id=address_id
    ).order_by(
        UtilityReading.service_id,
        UtilityReading.tariff_id,
        UtilityReading.period
    ).all()
    
    service_tariff_readings = {}
    for reading in readings:
        key = (reading.service_id, reading.tariff_id)
        if key not in service_tariff_readings:
            service_tariff_readings[key] = []
        service_tariff_readings[key].append(reading)
    
    for (service_id, tariff_id), readings_list in service_tariff_readings.items():
        tariff = db.session.query(UtilityTariff).filter_by(id=tariff_id).first()
        
        for i, reading in enumerate(readings_list):
            if i > 0 and tariff.tariff_type not in ['subscription', 'fixed', 'apartment']:
                reading.previous_reading = readings_list[i-1].current_reading
                reading.consumption = reading.current_reading - reading.previous_reading
            else:
                reading.previous_reading = reading.current_reading
                reading.consumption = 0
            
            # Розрахунок суми ТІЛЬКИ якщо не встановлена і не збережена з файлу
            if not preserve_amounts and (reading.amount is None or reading.amount == 0):
                if tariff.tariff_type == 'subscription':
                    reading.amount = tariff.rate
                elif tariff.tariff_type == 'fixed':
                    reading.amount = tariff.rate
                elif tariff.tariff_type == 'apartment':
                    # Для квартплати НЕ перераховуємо - залишаємо як є
                    pass
                else:
                    reading.amount = reading.consumption * tariff.rate if reading.consumption else 0
    
    db.session.commit()
    logger.info("✅ Розрахунки завершено")


def log_detailed_period_info(period, water_reading, gas_reading, electricity_day_reading=0, 
                           electricity_night_reading=0, electricity_reading=0, rent_amount=0, 
                           garbage_amount=0, water_consumption=0, water_amount=0, gas_consumption=0, 
                           gas_amount=0, format_type="karpat"):
    """Детальне логування показників для періоду"""
    if format_type == "karpat":
        # Формат для Карпатської Січі (показники + суми)
        logger.info(f"Період {period}: Вода={water_reading} (спож.={water_consumption:.1f}, сума={water_amount:.2f}), "
                   f"Газ={gas_reading} (спож.={gas_consumption:.1f}, сума={gas_amount:.2f}), "
                   f"Електрика_день={electricity_day_reading}, Електрика_ніч={electricity_night_reading}, "
                   f"Квартплата={rent_amount:.2f} грн, Сміття={garbage_amount:.2f} грн")
    elif format_type == "chornovola":
        # Формат для Чорновола (детальний з абонплатами)
        water_abon = 0  # TODO: обчислювати з тарифів
        gas_delivery = 0  # TODO: обчислювати з тарифів
        logger.info(f"Період {period}: Вода={water_reading} (спож.={water_consumption}, абон.={water_abon:.2f}, сума={water_amount:.2f}), "
                   f"Газ={gas_reading} (спож.={gas_consumption}, абон.={gas_delivery:.2f}, сума={gas_amount:.2f}), "
                   f"Світло={electricity_reading}, Квартплата={rent_amount:.2f} грн, Сміття={garbage_amount:.2f} грн")


def create_water_tariffs(water_service, water_subscription_start_date="2022-01-02"):
    """Створення тарифів для води (постачання, водовідведення, абонплата)"""
    # Тарифи для води - водопостачання
    water_supply_tariffs = [
        {'from': '2021-01-01', 'to': '2021-12-31', 'rate': 11.59},
        {'from': '2022-01-01', 'to': None, 'rate': 12.95}
    ]
    
    for data in water_supply_tariffs:
        get_or_create_tariff(
            service_id=water_service.id,
            name="Вода (постачання)",
            rate=data['rate'],
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='consumption',
            group_code='water',
            source='import'
        )
    
    # Тарифи для води - водовідведення
    water_wastewater_tariffs = [
        {'from': '2021-01-01', 'to': '2021-12-31', 'rate': 13.66},
        {'from': '2022-01-01', 'to': None, 'rate': 15.29}
    ]
    
    for data in water_wastewater_tariffs:
        get_or_create_tariff(
            service_id=water_service.id,
            name="Вода (водовідведення)",
            rate=data['rate'],
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='wastewater',
            group_code='water',
            source='import'
        )
    
    # Абонплата за воду (починається з вказаної дати - з оплати за січень 2022)
    water_subscription_tariffs = [
        {'from': water_subscription_start_date, 'to': '2022-04-01', 'rate': 14.17},
        {'from': '2022-04-01', 'to': None, 'rate': 24.67}
    ]
    
    for data in water_subscription_tariffs:
        get_or_create_tariff(
            service_id=water_service.id,
            name="Абонплата (вода)",
            rate=data['rate'],
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='subscription',
            group_code='water',
            source='import'
        )


def create_gas_tariffs(gas_service, gas_subscription_periods):
    """Створення тарифів для газу"""
    # Основний тариф для газу
    get_or_create_tariff(
        service_id=gas_service.id,
        name="Газ",
        rate=7.99,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='consumption',
        group_code='gas',
        source='import'
    )
    
    # Абонплата за газ (динамічна з періодів)
    for period in gas_subscription_periods:
        get_or_create_tariff(
            service_id=gas_service.id,
            name="Доставлення газу",
            rate=period['fee'],
            currency='UAH',
            valid_from=period['from'],
            valid_to=period['to'],
            is_active=period['to'] is None,
            tariff_type='subscription',
            group_code='gas',
            source='import'
        )
        logger.info(f"Створено абонплату газу {period['fee']} грн з {period['from'].strftime('%Y-%m-%d')}")


def import_water_readings(water_service, water_reading, period, date, user_id):
    """Імпорт показників води з усіма відповідними тарифами"""
    if water_reading > 0:
        water_tariffs = db.session.query(UtilityTariff).filter(
            UtilityTariff.service_id == water_service.id,
            UtilityTariff.valid_from <= date,
            or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
        ).all()
        
        imported_count = 0
        for tariff in water_tariffs:
            reading_value = 0 if tariff.tariff_type == 'subscription' else water_reading
            
            reading = UtilityReading(
                user_id=user_id,
                address_id=water_service.address_id,
                service_id=water_service.id,
                tariff_id=tariff.id,
                period=period,
                current_reading=reading_value,
                reading_date=date,
                is_paid=True
            )
            db.session.add(reading)
            imported_count += 1
        
        return imported_count
    return 0


def import_gas_readings(gas_service, gas_reading, period, date, user_id):
    """Імпорт показників газу з усіма відповідними тарифами"""
    if gas_reading > 0:
        gas_tariffs = db.session.query(UtilityTariff).filter(
            UtilityTariff.service_id == gas_service.id,
            UtilityTariff.valid_from <= date,
            or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
        ).all()
        
        imported_count = 0
        for tariff in gas_tariffs:
            reading = UtilityReading(
                user_id=user_id,
                address_id=gas_service.address_id,
                service_id=gas_service.id,
                tariff_id=tariff.id,
                period=period,
                current_reading=gas_reading if tariff.tariff_type == 'consumption' else 0,
                reading_date=date,
                is_paid=True
            )
            db.session.add(reading)
            imported_count += 1
        
        return imported_count
    return 0