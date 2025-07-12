#!/usr/bin/env python3
"""
Скрипт імпорту комунальних показників з ODS файлу для адреси Карпатської Січі 6Б/27
Версія 3.0 - з динамічним створенням тарифів та правильними датами
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

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константи
ADDRESS_NAME = "Карпатської Січі 6Б, кв. 27"  # Використовуємо існуючу адресу з ID 35
ADDRESS_FULL = "м. Івано-Франківськ, вул. Карпатської Січі 6Б, кв. 27"
USER_ID = 1


def get_cell_value(value):
    """Отримати значення з комірки Excel"""
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_number(value):
    """Парсинг числа з рядка"""
    if not value or value == '0':
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
        fee = parse_number(get_cell_value(fee_value)) if not pd.isna(fee_value) else 0
            
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
            has_shared_meter=False,  # НЕ спільний показник!
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
            has_shared_meter=False,  # НЕ спільний показник!
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
    # Шукаємо існуючий тариф за УНІКАЛЬНИМ ІНДЕКСОМ: service_id, name, valid_from
    existing_tariff = db.session.query(UtilityTariff).filter(
        UtilityTariff.service_id == service_id,
        UtilityTariff.name == name,
        UtilityTariff.valid_from == valid_from
    ).first()
    
    if existing_tariff:
        logger.info(f"Використовуємо існуючий тариф: {name} (ID: {existing_tariff.id})")
        # Оновлюємо поля якщо потрібно
        existing_tariff.rate = rate
        existing_tariff.currency = currency
        existing_tariff.valid_to = valid_to
        existing_tariff.is_active = is_active
        existing_tariff.tariff_type = tariff_type
        existing_tariff.group_code = group_code
        existing_tariff.source = source
        return existing_tariff
    else:
        # Створюємо новий тариф
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
    
    # Тарифи для води - водопостачання (змінювались)
    water_supply_tariffs = [
        {'from': '2021-01-01', 'to': '2022-01-01', 'rate': 11.59},
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
    
    # Тарифи для води - водовідведення (змінювались)
    water_wastewater_tariffs = [
        {'from': '2021-01-01', 'to': '2022-01-01', 'rate': 13.66},
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
    
    # Абонплата за воду (змінювалась)
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
    
    # Тариф для газу (ПОСТІЙНИЙ)
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
    
    # Тариф для квартплати (єдиний зі ставкою 1)
    get_or_create_tariff(
        service_id=services['rent'].id,
        name="Квартплата",
        rate=1.0,  # Ставка 1, щоб сума дорівнювала введеній
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='apartment',
        group_code=None,
        source='import'
    )
    
    # Тариф для сміття (єдиний зі ставкою 1)
    get_or_create_tariff(
        service_id=services['garbage'].id,
        name="Фіксований",
        rate=1.0,  # Ставка 1, щоб сума дорівнювала введеній
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


def create_reading(user_id, address_id, service_id, tariff_id, period, current_reading, amount, reading_date, is_paid):
    """Створити новий показник"""
    new_reading = UtilityReading(
        user_id=user_id,
        address_id=address_id,
        service_id=service_id,
        tariff_id=tariff_id,
        period=period,
        current_reading=current_reading,
        amount=amount,
        reading_date=reading_date,
        is_paid=is_paid
    )
    db.session.add(new_reading)
    return new_reading


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
        water_reading = parse_number(get_cell_value(df.iloc[i, 1]))      # Кол.1: Вода
        gas_reading = parse_number(get_cell_value(df.iloc[i, 7]))        # Кол.7: Газ  
        electricity_day_reading = parse_number(get_cell_value(df.iloc[i, 11]))   # Кол.11: Електрика день
        electricity_night_reading = parse_number(get_cell_value(df.iloc[i, 12])) # Кол.12: Електрика ніч
        
        # Квартплата та сміття (суми, а не показники)
        rent_amount = 0
        garbage_amount = 0
        
        if len(df.columns) > 14:
            rent_amount = parse_number(get_cell_value(df.iloc[i, 14]))   # Кол.14: Квартплата
            # Логування для діагностики квартплати
            if rent_amount != 0:
                logger.info(f"Період {period}: квартплата raw='{get_cell_value(df.iloc[i, 14])}' parsed={rent_amount}")
            
        if len(df.columns) > 16:
            garbage_amount = parse_number(get_cell_value(df.iloc[i, 16])) # Кол.16: Сміття
        
        # Створюємо показники для води
        if water_reading > 0:
            water_tariffs = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['water'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).all()
            
            for tariff in water_tariffs:
                # Для абонплати показник завжди 0
                reading_value = 0 if tariff.tariff_type == 'subscription' else water_reading
                
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['water'].address_id,
                    service_id=services['water'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=reading_value,
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
        
        # Створюємо показники для газу
        if gas_reading > 0:
            gas_tariffs = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['gas'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).all()
            
            for tariff in gas_tariffs:
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['gas'].address_id,
                    service_id=services['gas'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=gas_reading if tariff.tariff_type == 'consumption' else 0,
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
                    current_reading=0,  # Для квартплати ставимо 0
                    amount=rent_amount,
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
                    current_reading=0,  # Для сміття ставимо 0
                    amount=garbage_amount,
                    reading_date=date,
                    is_paid=True
                )
                db.session.add(reading)
                imported_count += 1
    
    db.session.commit()
    logger.info(f"Імпортовано {imported_count} показників")
    return imported_count


def calculate_previous_readings_and_amounts(address_id):
    """Розрахунок попередніх показників та сум"""
    logger.info("Розрахунок попередніх показників та сум...")
    
    # Отримуємо всі показники для адреси
    readings = db.session.query(UtilityReading).filter_by(
        address_id=address_id
    ).order_by(
        UtilityReading.service_id,
        UtilityReading.tariff_id,
        UtilityReading.period
    ).all()
    
    # Групуємо по службі та тарифу
    service_tariff_readings = {}
    for reading in readings:
        key = (reading.service_id, reading.tariff_id)
        if key not in service_tariff_readings:
            service_tariff_readings[key] = []
        service_tariff_readings[key].append(reading)
    
    # Розраховуємо для кожної групи
    for (service_id, tariff_id), readings_list in service_tariff_readings.items():
        tariff = db.session.query(UtilityTariff).filter_by(id=tariff_id).first()
        
        for i, reading in enumerate(readings_list):
            # Попередній показник та споживання
            if i > 0 and tariff.tariff_type not in ['subscription', 'fixed', 'apartment']:
                reading.previous_reading = readings_list[i-1].current_reading
                reading.consumption = reading.current_reading - reading.previous_reading
            else:
                reading.previous_reading = reading.current_reading
                reading.consumption = 0
            
            # Розрахунок суми
            if tariff.tariff_type == 'subscription':
                # Для абонплати сума = тариф
                reading.amount = tariff.rate
            elif tariff.tariff_type == 'fixed':
                # Для фіксованих платежів сума = тариф
                reading.amount = tariff.rate
            elif tariff.tariff_type == 'apartment':
                # Для квартплати сума залишається як є (вже встановлена при імпорті)
                pass  # Не перераховуємо суму
            else:
                # Для споживання сума = споживання * тариф
                reading.amount = reading.consumption * tariff.rate if reading.consumption else 0
    
    db.session.commit()
    logger.info("✅ Розрахунки завершено")


def main():
    """Головна функція"""
    try:
        logger.info("Початок імпорту комунальних даних для адреси Карпатської Січі 6Б/27")
        
        # Знаходимо адресу Карпатської Січі
        address = db.session.query(UtilityAddress).filter_by(
            user_id=USER_ID, 
            name=ADDRESS_NAME
        ).first()
        
        if address:
            # Знаходимо всі службі для цієї адреси
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
        
        # Розраховуємо попередні показники та суми
        calculate_previous_readings_and_amounts(address.id)
        
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