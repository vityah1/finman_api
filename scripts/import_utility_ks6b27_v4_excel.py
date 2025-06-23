#!/usr/bin/env python3
"""
Скрипт імпорту комунальних показників з Excel файлу для адреси Карпатської Січі 6Б/27
Версія 4.0 - для Excel формату з правильним читанням колонок
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import logging
import traceback

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import or_, and_

from models.models import UtilityAddress, UtilityService, UtilityTariff, UtilityReading
from mydb import db, engine
from scripts.utility_import_common import (
    parse_number, create_or_get_address, get_or_create_tariff, 
    analyze_gas_subscription_fees, clean_existing_data, 
    calculate_previous_readings_and_amounts, create_water_tariffs, 
    create_gas_tariffs, import_water_readings, import_gas_readings,
    log_detailed_period_info
)

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константи
ADDRESS_NAME = "Карпатської Січі 6Б, кв. 27"
ADDRESS_FULL = "м. Івано-Франківськ, вул. Карпатської Січі 6Б, кв. 27"
USER_ID = 1

def parse_number(value):
    """Парсинг числа з рядка"""
    if pd.isna(value) or value == '' or value == 0:
        return 0
    
    # Конвертуємо в рядок якщо потрібно
    value = str(value).strip()
    
    # Зберігаємо знак
    is_negative = value.startswith('-')
    if is_negative:
        value = value[1:]
    
    # Видаляємо непотрібні символи (валюти, текст)
    import re
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

def analyze_gas_subscription_fees(df):
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
        
        # Абонплата газу в колонці 9
        fee_value = df.iloc[i, 9] if len(df.columns) > 9 else None
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

def create_or_get_address():
    """Створити або отримати адресу"""
    # Шукаємо по повній адресі
    address = db.session.query(UtilityAddress).filter_by(
        address=ADDRESS_FULL,
        user_id=USER_ID
    ).first()
    
    if not address:
        # Якщо не знайшли, шукаємо по назві
        address = db.session.query(UtilityAddress).filter_by(
            name=ADDRESS_NAME,
            user_id=USER_ID
        ).first()
    
    if not address:
        address = UtilityAddress(
            user_id=USER_ID,
            name=ADDRESS_NAME,
            address=ADDRESS_FULL
        )
        db.session.add(address)
        db.session.commit()
        logger.info(f"Створено адресу: {ADDRESS_NAME}")
    else:
        logger.info(f"Знайдено існуючу адресу: {ADDRESS_NAME} (ID: {address.id})")
    
    return address

def create_services(address_id):
    """Створити служби"""
    services = {}
    
    # Перевіряємо існуючі служби
    existing_services = db.session.query(UtilityService).filter_by(address_id=address_id).all()
    for service in existing_services:
        if service.name == 'Вода':
            services['water'] = service
        elif service.name == 'Газ':
            services['gas'] = service
        elif service.name == 'Електрика (день)':
            services['electricity_day'] = service
        elif service.name == 'Електрика (ніч)':
            services['electricity_night'] = service
        elif service.name == 'Квартплата':
            services['rent'] = service
        elif service.name == 'Сміття':
            services['garbage'] = service
    
    # Створюємо відсутні служби
    if 'water' not in services:
        water = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Вода",
            unit="м³",
            is_active=True,
            has_shared_meter=True,
            service_group="water"
        )
        db.session.add(water)
        services['water'] = water
        logger.info(f"Створено службу: Вода")
    
    if 'gas' not in services:
        gas = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Газ",
            unit="м³",
            is_active=True,
            has_shared_meter=True,
            service_group="gas"
        )
        db.session.add(gas)
        services['gas'] = gas
        logger.info(f"Створено службу: Газ")
    
    if 'electricity_day' not in services:
        electricity_day = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Електрика (день)",
            unit="кВт·год",
            is_active=True,
            has_shared_meter=False,
            service_group="electricity"
        )
        db.session.add(electricity_day)
        services['electricity_day'] = electricity_day
        logger.info(f"Створено службу: Електрика (день)")
    
    if 'electricity_night' not in services:
        electricity_night = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Електрика (ніч)",
            unit="кВт·год",
            is_active=True,
            has_shared_meter=False,
            service_group="electricity"
        )
        db.session.add(electricity_night)
        services['electricity_night'] = electricity_night
        logger.info(f"Створено службу: Електрика (ніч)")
    
    if 'rent' not in services:
        rent = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Квартплата",
            unit="грн",
            is_active=True,
            has_shared_meter=False
        )
        db.session.add(rent)
        services['rent'] = rent
        logger.info(f"Створено службу: Квартплата")
    
    if 'garbage' not in services:
        garbage = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Сміття",
            unit="грн",
            is_active=True,
            has_shared_meter=False
        )
        db.session.add(garbage)
        services['garbage'] = garbage
        logger.info(f"Створено службу: Сміття")
    
    db.session.commit()
    return services

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
        existing_tariff.tariff_type = tariff_type
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

def create_tariffs(services, gas_subscription_periods):
    """Створити тарифи для всіх служб"""
    
    logger.info("Створення нових тарифів...")
    
    # Тарифи для води - водопостачання
    water_supply_tariffs = [
        {'from': '2021-01-01', 'to': '2021-12-31', 'rate': 11.59},
        {'from': '2022-01-01', 'to': None, 'rate': 12.95}
    ]
    
    for data in water_supply_tariffs:
        get_or_create_tariff(
            service_id=services['water'].id,
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
            service_id=services['water'].id,
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
    
    # Абонплата за воду (змінювалась) - починається з 2022 року
    water_subscription_tariffs = [
        {'from': '2022-01-01', 'to': '2022-04-01', 'rate': 14.17},
        {'from': '2022-04-01', 'to': None, 'rate': 24.67}
    ]
    
    for data in water_subscription_tariffs:
        get_or_create_tariff(
            service_id=services['water'].id,
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
    
    # Тариф для газу
    get_or_create_tariff(
        service_id=services['gas'].id,
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
            service_id=services['gas'].id,
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
    
    # Тарифи для електрики
    get_or_create_tariff(
        service_id=services['electricity_day'].id,
        name="Електроенергія (день)",
        rate=4.32,
        currency='UAH',
        valid_from=datetime.strptime('2024-06-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='consumption',
        group_code='electricity',
        source='import'
    )
    
    get_or_create_tariff(
        service_id=services['electricity_night'].id,
        name="Електроенергія (ніч)",
        rate=2.16,
        currency='UAH',
        valid_from=datetime.strptime('2024-06-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='consumption',
        group_code='electricity',
        source='import'
    )
    
    # Тариф для квартплати
    get_or_create_tariff(
        service_id=services['rent'].id,
        name="Квартплата",
        rate=1.0,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='apartment',
        group_code=None,
        source='import'
    )
    
    # Тариф для сміття
    get_or_create_tariff(
        service_id=services['garbage'].id,
        name="Фіксований",
        rate=1.0,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='fixed',
        group_code='garbage',
        source='import'
    )
    
    logger.info("Створено/оновлено всі тарифи")
    return {}

def import_readings(services, df):
    """Імпортувати показники з Excel файлу"""
    
    imported_count = 0
    
    for i in range(len(df)):
        if i < 5:  # Пропускаємо заголовки (перші 5 рядків)
            continue
            
        # Парсимо дату
        date_value = df.iloc[i, 0]  # Колонка 0 - дата
        if pd.isna(date_value):
            continue
            
        try:
            if isinstance(date_value, str):
                date = datetime.strptime(date_value, '%d.%m.%Y')
            else:
                date = date_value
            # ВАЖЛИВО: показники станом на 01.05.2025 - це дані за КВІТЕНЬ!
            period_date = date - relativedelta(months=1)
            period = period_date.strftime('%Y-%m')
        except:
            continue
        
        # Показники з правильних колонок Excel структури
        water_reading = parse_number(df.iloc[i, 1])      # Кол.1: Показник води
        water_consumption = parse_number(df.iloc[i, 2])  # Кол.2: Споживання води
        water_amount = parse_number(df.iloc[i, 3])       # Кол.3: Сума води до оплати
        
        gas_reading = parse_number(df.iloc[i, 7])        # Кол.7: Показник газу
        gas_consumption = parse_number(df.iloc[i, 8])    # Кол.8: Споживання газу
        gas_subscription = parse_number(df.iloc[i, 9])   # Кол.9: Абонплата газу
        gas_amount = parse_number(df.iloc[i, 10])        # Кол.10: Сума газу до оплати
        
        electricity_day_reading = parse_number(df.iloc[i, 11])   # Кол.11: Електрика день
        electricity_night_reading = parse_number(df.iloc[i, 12]) # Кол.12: Електрика ніч
        
        # Квартплата та сміття (суми, а не показники)
        rent_amount = 0
        garbage_amount = 0
        
        if len(df.columns) > 14:
            rent_amount = parse_number(df.iloc[i, 14])   # Кол.14: Квартплата
            
        if len(df.columns) > 16:
            garbage_amount = parse_number(df.iloc[i, 16]) # Кол.16: Сміття
        
        # Використовуємо реальні значення з файлу для логування
        
        log_detailed_period_info(
            period=period,
            water_reading=water_reading,
            gas_reading=gas_reading, 
            electricity_day_reading=electricity_day_reading,
            electricity_night_reading=electricity_night_reading,
            rent_amount=rent_amount,
            garbage_amount=garbage_amount,
            water_consumption=water_consumption,
            water_amount=water_amount,
            gas_consumption=gas_consumption,
            gas_amount=gas_amount,
            format_type="karpat"
        )
        
        # Створюємо показники для води
        if water_reading > 0:
            water_tariffs = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['water'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).all()
            
            logger.info(f"  Вода: знайдено {len(water_tariffs)} тарифів для дати {date.strftime('%Y-%m-%d')}")
            for t in water_tariffs:
                logger.info(f"    - {t.name} ({t.tariff_type})")
            
            if len(water_tariffs) == 0:
                # Якщо немає тарифів для дати (2021 періоди), створюємо записи з активними тарифами
                logger.info(f"  Немає тарифів для {period}, створюємо записи з активними тарифами")
                active_water_tariffs = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id == services['water'].id,
                    UtilityTariff.is_active == True,
                    UtilityTariff.tariff_type != 'subscription'  # Без абонплати для старих періодів
                ).all()
                
                if active_water_tariffs and water_consumption > 0:
                    for tariff in active_water_tariffs:
                        # Розраховуємо суму на основі споживання і тарифу
                        calculated_amount = water_consumption * tariff.rate
                        
                        reading = UtilityReading(
                            user_id=USER_ID,
                            address_id=services['water'].address_id,
                            service_id=services['water'].id,
                            tariff_id=tariff.id,
                            period=period,
                            current_reading=water_reading,
                            consumption=water_consumption,
                            amount=calculated_amount,  # Розраховуємо на основі тарифу
                            reading_date=date,
                            is_paid=True
                        )
                        db.session.add(reading)
                        imported_count += 1
                        logger.info(f"  Додано запис води: тариф={tariff.name}, показник={water_reading}, споживання={water_consumption}, сума={calculated_amount:.2f} (тариф={tariff.rate})")
            else:
                # Розраховуємо суми правильно на основі тарифів і споживання
                for tariff in water_tariffs:
                    if tariff.tariff_type == 'subscription':
                        # Для абонплати використовуємо тариф
                        reading_value = 0
                        consumption = 0
                        amount = tariff.rate
                    else:
                        # Для споживання розраховуємо на основі споживання і тарифу
                        reading_value = water_reading
                        consumption = water_consumption
                        amount = water_consumption * tariff.rate if water_consumption > 0 else 0
                    
                    reading = UtilityReading(
                        user_id=USER_ID,
                        address_id=services['water'].address_id,
                        service_id=services['water'].id,
                        tariff_id=tariff.id,
                        period=period,
                        current_reading=reading_value,
                        consumption=consumption,
                        amount=amount,
                        reading_date=date,
                        is_paid=True
                    )
                    db.session.add(reading)
                    imported_count += 1
                    logger.info(f"  Додано запис води: тариф={tariff.name}, показник={reading_value}, споживання={consumption}, сума={amount:.2f}")
        
        # Створюємо показники для газу
        if gas_reading > 0:
            gas_tariffs = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['gas'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).all()
            
            # Розподіляємо між споживанням та абонплатою
            consumption_amount = gas_amount - gas_subscription if gas_amount > gas_subscription else gas_amount
            
            for tariff in gas_tariffs:
                if tariff.tariff_type == 'consumption':
                    amount = consumption_amount
                    consumption = gas_consumption
                else:  # subscription
                    amount = gas_subscription 
                    consumption = 0
                    
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['gas'].address_id,
                    service_id=services['gas'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=gas_reading if tariff.tariff_type == 'consumption' else 0,
                    consumption=consumption,
                    amount=amount,  # Використовуємо готові суми з файлу
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
        
        # Створюємо показники для електрики (день)
        if electricity_day_reading > 0:
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['electricity_day'].id,
                UtilityTariff.is_active == True
            ).first()
            
            if tariff:
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['electricity_day'].address_id,
                    service_id=services['electricity_day'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=electricity_day_reading,
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
        
        # Створюємо показники для електрики (ніч)
        if electricity_night_reading > 0:
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['electricity_night'].id,
                UtilityTariff.is_active == True
            ).first()
            
            if tariff:
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['electricity_night'].address_id,
                    service_id=services['electricity_night'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=electricity_night_reading,
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
        
        # Створюємо запис для квартплати
        if rent_amount > 0:
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['rent'].id,
                UtilityTariff.is_active == True
            ).first()
            
            if tariff:
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['rent'].address_id,
                    service_id=services['rent'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=0,
                    amount=rent_amount,  # Зберігаємо суму напряму
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
        
        # Створюємо запис для сміття
        if garbage_amount > 0:
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['garbage'].id,
                UtilityTariff.is_active == True
            ).first()
            
            if tariff:
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['garbage'].address_id,
                    service_id=services['garbage'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=0,
                    amount=garbage_amount,  # Зберігаємо суму напряму
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
    
    db.session.commit()
    logger.info(f"Імпортовано {imported_count} показників")
    return imported_count


def main():
    """Головна функція"""
    try:
        logger.info("Початок імпорту комунальних даних для адреси Карпатської Січі 6Б/27 (Excel версія)")
        
        # Знаходимо адресу Карпатської Січі та очищаємо дані
        address = db.session.query(UtilityAddress).filter_by(
            user_id=USER_ID, 
            name=ADDRESS_NAME
        ).first()
        
        if address:
            # Знаходимо всі служби для цієї адреси
            services = db.session.query(UtilityService).filter_by(address_id=address.id).all()
            service_ids = [s.id for s in services]
            
            if service_ids:
                # КРОК 1: Знаходимо тарифи, які використовувались за травень 2025 (зберігаємо їх)
                may_2025_tariffs = db.session.query(UtilityTariff).join(UtilityReading).filter(
                    UtilityReading.period == '2025-05',
                    UtilityReading.user_id == USER_ID,
                    UtilityTariff.service_id.in_(service_ids)
                ).distinct().all()
                
                may_2025_tariff_ids = [t.id for t in may_2025_tariffs]
                logger.info(f"Знайдено тарифів за травень 2025 (зберігаємо): {len(may_2025_tariffs)} (IDs: {may_2025_tariff_ids})")
                
                # КРОК 2: Спочатку видаляємо ВСІ показники крім травня 2025
                deleted_readings = db.session.query(UtilityReading).filter(
                    UtilityReading.service_id.in_(service_ids),
                    UtilityReading.user_id == USER_ID,
                    UtilityReading.period != '2025-05'  # Зберігаємо тільки травень 2025
                ).delete(synchronize_session=False)
                db.session.commit()
                logger.info(f"Видалено {deleted_readings} показників (збережено травень 2025)")
                
                # КРОК 3: Тепер видаляємо тарифи, крім тих що використовувались за травень 2025
                if may_2025_tariff_ids:
                    # Видаляємо всі тарифи крім тих що використовувались за травень 2025
                    deleted_tariffs = db.session.query(UtilityTariff).filter(
                        UtilityTariff.service_id.in_(service_ids),
                        ~UtilityTariff.id.in_(may_2025_tariff_ids)
                    ).delete(synchronize_session=False)
                else:
                    # Якщо немає тарифів за травень 2025, видаляємо всі тарифи для цих сервісів
                    deleted_tariffs = db.session.query(UtilityTariff).filter(
                        UtilityTariff.service_id.in_(service_ids)
                    ).delete(synchronize_session=False)
                
                db.session.commit()
                logger.info(f"Видалено {deleted_tariffs} тарифів (збережено тарифи за травень 2025: {len(may_2025_tariff_ids)})")
            else:
                logger.info("Служби не знайдені для цієї адреси")
        else:
            logger.info("Адреса не знайдена, буде створена нова")
        
        # Завантажуємо Excel файл
        df = pd.read_excel("scripts/utility_ks6b27.xlsx", header=None)
        logger.info(f"Завантажено Excel файл: {df.shape[0]} рядків, {df.shape[1]} колонок")
        
        # Аналізуємо зміни абонплати газу
        logger.info("Аналіз абонплати газу...")
        gas_subscription_periods = analyze_gas_subscription_fees(df)
        logger.info(f"Знайдено {len(gas_subscription_periods)} періодів абонплати")
        
        # Створюємо адресу
        address = create_or_get_address()
        
        # Створюємо служби
        logger.info("Створення служб...")
        services = create_services(address.id)
        
        # Створюємо тарифи
        logger.info("Створення тарифів...")
        create_tariffs(services, gas_subscription_periods)
        
        # Імпортуємо показники
        logger.info("Імпорт показників...")
        imported_count = import_readings(services, df)
        
        # Розраховуємо попередні показники та суми (зберігаємо готові суми з файлу)
        calculate_previous_readings_and_amounts(address.id, preserve_amounts=True)
        
        logger.info(f"Імпорт завершено успішно! Імпортовано {imported_count} записів")
        
        # Очищаємо кеш SQLAlchemy
        db.session.close()
        db.session.remove()
        engine.dispose()
        logger.info("✅ Кеш БД очищено")
        
    except Exception as e:
        logger.error(f"Помилка під час імпорту: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        db.session.close()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())