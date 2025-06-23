#!/usr/bin/env python3
"""
Скрипт імпорту комунальних показників з Excel файлу для адреси Чорновола 94/31
Excel версія з збереженням всієї логіки очищення та перевірок
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
from sqlalchemy.pool import NullPool

from models.models import UtilityAddress, UtilityService, UtilityTariff, UtilityReading
from mydb import db, engine

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константи
ADDRESS_NAME = "Чорновола 94, кв. 31"
ADDRESS_FULL = "м. Івано-Франківськ, вул. Чорновола 94, кв. 31"
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
            address=ADDRESS_FULL,
            source='import'
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
        elif service.name == 'Світло':
            services['electricity'] = service
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
            service_group="water",
            source='import'
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
            service_group="gas",
            source='import'
        )
        db.session.add(gas)
        services['gas'] = gas
        logger.info(f"Створено службу: Газ")
    
    if 'electricity' not in services:
        electricity = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Світло",
            unit="кВт·год",
            is_active=True,
            has_shared_meter=False,  # На Чорновола один лічильник, не спільний
            service_group="electricity",
            source='import'
        )
        db.session.add(electricity)
        services['electricity'] = electricity
        logger.info(f"Створено службу: Світло")
    else:
        # Оновлюємо існуючу службу
        services['electricity'].has_shared_meter = False
        logger.info(f"Оновлено службу Світло: has_shared_meter=False")    
    if 'rent' not in services:
        rent = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Квартплата",
            unit="грн",
            is_active=True,
            has_shared_meter=False,
            source='import'
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
            has_shared_meter=False,
            source='import'
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

def create_tariffs(services):
    """Створити тарифи для всіх служб"""
    
    # КРОК 1: Знаходимо тарифи, які використовувались за травень 2025 (зберігаємо їх)
    service_ids = [s.id for s in services.values()]
    may_2025_tariffs = db.session.query(UtilityTariff).join(UtilityReading).filter(
        UtilityReading.period == '2025-05',
        UtilityReading.user_id == USER_ID,
        UtilityTariff.service_id.in_(service_ids)
    ).distinct().all()
    
    may_2025_tariff_ids = [t.id for t in may_2025_tariffs]
    logger.info(f"Знайдено тарифів за травень 2025 (зберігаємо): {len(may_2025_tariffs)} (IDs: {may_2025_tariff_ids})")
    
    # КРОК 2: Спочатку видаляємо ВСІ показники крім травня 2025 (щоб зняти foreign key constraint)
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
    
    # КРОК 4: Тепер створюємо нові тарифи
    logger.info("Створення нових тарифів...")
    
    # Тарифи для води - водопостачання (змінювались)
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
    
    # Тарифи для води - водовідведення (змінювались)
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
    
    # Тариф для газу (ПОСТІЙНИЙ з PDF справа)
    get_or_create_tariff(
        service_id=services['gas'].id,
        name="Газ",
        rate=7.99,  # Постійний тариф з PDF
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        valid_to=None,
        is_active=True,
        tariff_type='consumption',
        group_code='gas',
        source='import'
    )
    
    # Абонплата за газ (доставлення) - змінювалась
    gas_subscription_tariffs = [
        {'from': '2021-11-01', 'to': '2021-12-01', 'rate': 0},
        {'from': '2021-12-01', 'to': '2022-01-01', 'rate': 43.28},
        {'from': '2022-01-01', 'to': '2022-09-01', 'rate': 23.44},
        {'from': '2022-09-01', 'to': '2022-10-01', 'rate': 107.28},  # компенсація
        {'from': '2022-10-01', 'to': '2024-01-01', 'rate': 23.44},
        {'from': '2024-01-01', 'to': None, 'rate': 58.4}
    ]
    
    for data in gas_subscription_tariffs:
        get_or_create_tariff(
            service_id=services['gas'].id,
            name="Доставлення газу",
            rate=data['rate'],
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='subscription',
            group_code='gas',
            source='import'
        )    
    # Тарифи для електрики (змінювались кілька разів)
    electricity_tariffs = [
        {'from': '2021-01-01', 'to': '2023-06-01', 'rate': 1.44},  # До 250 кВт
        {'from': '2023-06-01', 'to': '2024-06-01', 'rate': 2.64},
        {'from': '2024-06-01', 'to': None, 'rate': 4.32}
    ]
    
    for data in electricity_tariffs:
        get_or_create_tariff(
            service_id=services['electricity'].id,
            name="Електроенергія",
            rate=data['rate'],
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
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
    
    # Тарифи для сміття - змінювались
    garbage_tariffs = [
        {'from': '2021-11-01', 'to': '2021-12-01', 'rate': 0},
        {'from': '2021-12-01', 'to': '2022-09-01', 'rate': 22.54},
        {'from': '2022-09-01', 'to': '2022-10-01', 'rate': 107.28},  # компенсація
        {'from': '2022-10-01', 'to': None, 'rate': 37.2}
    ]
    
    for data in garbage_tariffs:
        get_or_create_tariff(
            service_id=services['garbage'].id,
            name="Фіксований",
            rate=data['rate'],
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='fixed',
            group_code='garbage',
            source='import'
        )
    
    logger.info("Створено/оновлено всі тарифи")
    return {}

def import_readings(services, df):
    """Імпортувати показники з Excel файлу"""
    
    # Спочатку визначаємо які періоди є у файлі
    file_periods = set()
    for i in range(len(df)):
        if i < 4:  # Пропускаємо заголовки (4 рядки)
            continue
            
        date_value = df.iloc[i, 0]  # Колонка 0 - дата
        if pd.isna(date_value):
            continue
            
        try:
            if isinstance(date_value, str):
                date = datetime.strptime(date_value, '%d.%m.%Y')
            else:
                date = date_value
            period_date = date - relativedelta(months=1)
            period = period_date.strftime('%Y-%m')
            file_periods.add(period)
        except:
            continue
    
    logger.info(f"Знайдено періоди у файлі: {sorted(file_periods)}")
    
    # КРОК: Видаляємо існуючі показники за періоди що імпортуються (крім травня 2025)
    service_ids = [s.id for s in services.values()]
    periods_to_delete = [p for p in file_periods if p != '2025-05']  # Зберігаємо травень 2025
    
    if periods_to_delete:
        deleted_readings = db.session.query(UtilityReading).filter(
            UtilityReading.service_id.in_(service_ids),
            UtilityReading.user_id == USER_ID,
            UtilityReading.period.in_(periods_to_delete)
        ).delete(synchronize_session=False)
        db.session.commit()
        logger.info(f"Видалено {deleted_readings} показників за періоди: {sorted(periods_to_delete)}")
    
    imported_count = 0
    processed_periods = set()  # Для відстеження вже оброблених періодів
    
    # Функція для створення показника
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
    
    for i in range(len(df)):
        if i < 4:  # Пропускаємо заголовки (4 рядки в Excel)
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
        
        # Пропускаємо, якщо цей період вже оброблено
        if period in processed_periods:
            logger.warning(f"Пропускаємо дублюючий період: {period}")
            continue
        processed_periods.add(period)        
        
        # Показники з правильних колонок Excel структури (з аналізу)
        water_reading = parse_number(df.iloc[i, 1])        # Кол.1: показник води
        water_consumption = parse_number(df.iloc[i, 2])    # Кол.2: споживання води
        water_abon = parse_number(df.iloc[i, 3])           # Кол.3: абонплата води
        water_amount = parse_number(df.iloc[i, 4])         # Кол.4: сума за воду
        gas_reading = parse_number(df.iloc[i, 6])          # Кол.6: показник газу
        gas_consumption = parse_number(df.iloc[i, 7])      # Кол.7: споживання газу
        gas_delivery = parse_number(df.iloc[i, 8])         # Кол.8: доставлення (АБОНПЛАТА)
        gas_amount = parse_number(df.iloc[i, 9])           # Кол.9: сума за споживання
        rent_amount = parse_number(df.iloc[i, 11])         # Кол.11: квартплата
        garbage_amount = parse_number(df.iloc[i, 13])      # Кол.13: сміття
        electricity_reading = parse_number(df.iloc[i, 15]) # Кол.15: показник світла
        
        # Загальне логування всіх показників для періоду
        logger.info(f"Період {period}: Вода={water_reading} (спож.={water_consumption}, абон.={water_abon:.2f}, сума={water_amount:.2f}), Газ={gas_reading} (спож.={gas_consumption}, абон.={gas_delivery:.2f}, сума={gas_amount:.2f}), Світло={electricity_reading}, Квартплата={rent_amount:.2f} грн, Сміття={garbage_amount:.2f} грн")
        
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
                
                # Для абонплати води з березня 2024 використовуємо значення з колонки 3
                if tariff.tariff_type == 'subscription' and water_abon > 0:
                    amount = water_abon
                else:
                    amount = None
                
                reading = create_reading(
                    user_id=USER_ID,
                    address_id=services['water'].address_id,
                    service_id=services['water'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=reading_value,
                    amount=amount,
                    reading_date=date,
                    is_paid=True
                )
                imported_count += 1        
        # Створюємо показники для газу
        if gas_reading > 0:
            gas_tariffs = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['gas'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).all()
            
            for tariff in gas_tariffs:
                reading = create_reading(
                    user_id=USER_ID,
                    address_id=services['gas'].address_id,
                    service_id=services['gas'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=gas_reading if tariff.tariff_type == 'consumption' else 0,
                    amount=None,
                    reading_date=date,
                    is_paid=True
                )
                imported_count += 1
        
        # Створюємо показники для електрики (єдиний тариф)
        if electricity_reading > 0:
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['electricity'].id,
                UtilityTariff.is_active == True
            ).first()
            
            if tariff:
                reading = create_reading(
                    user_id=USER_ID,
                    address_id=services['electricity'].address_id,
                    service_id=services['electricity'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=electricity_reading,
                    amount=None,
                    reading_date=date,
                    is_paid=True
                )
                imported_count += 1        
        # Створюємо запис для квартплати (використовуємо єдиний тариф зі ставкою 1)
        if rent_amount != 0:  # Дозволяємо і від'ємні значення
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['rent'].id,
                UtilityTariff.name == "Квартплата"
            ).first()
            
            if tariff:
                reading = create_reading(
                    user_id=USER_ID,
                    address_id=services['rent'].address_id,
                    service_id=services['rent'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=rent_amount,  # Зберігаємо суму як показник
                    amount=rent_amount,  # Сума дорівнює показнику * 1
                    reading_date=date,
                    is_paid=True
                )
                imported_count += 1
        
        # Створюємо запис для сміття
        if garbage_amount >= 0:  # Включаємо і 0
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['garbage'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).first()
            
            if tariff:
                reading = create_reading(
                    user_id=USER_ID,
                    address_id=services['garbage'].address_id,
                    service_id=services['garbage'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=0,
                    amount=garbage_amount,
                    reading_date=date,
                    is_paid=True
                )
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
            
            # Розрахунок суми ТІЛЬКИ якщо не встановлена
            if reading.amount is None or reading.amount == 0:
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
        logger.info("Початок імпорту комунальних даних для адреси Чорновола 94/31 (Excel версія)")
        
        # Завантажуємо Excel файл
        df = pd.read_excel("scripts/utility_chornovola_94_31.xlsx", header=None)
        logger.info(f"Завантажено Excel файл: {df.shape[0]} рядків, {df.shape[1]} колонок")
        
        # Створюємо адресу
        address = create_or_get_address()
        
        # Створюємо служби
        logger.info("Створення служб...")
        services = create_services(address.id)
        
        # Створюємо тарифи (з логікою очищення всередині)
        logger.info("Створення тарифів...")
        create_tariffs(services)
        
        # Імпортуємо показники
        logger.info("Імпорт показників...")
        imported_count = import_readings(services, df)
        
        # Розраховуємо попередні показники та суми
        calculate_previous_readings_and_amounts(address.id)
        
        # Фінальний commit та очищення сесії
        db.session.commit()
        db.session.close()
        
        # Очищаємо кеш SQLAlchemy
        db.session.remove()
        engine.dispose()
        
        logger.info(f"Імпорт завершено успішно! Імпортовано {imported_count} записів")
        logger.info("✅ Кеш БД очищено")
        
    except Exception as e:
        logger.error(f"Помилка під час імпорту: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        db.session.close()
        return 1
    finally:
        # Гарантуємо закриття сесії
        if db.session.is_active:
            db.session.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())