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

from odf import opendocument
from odf.table import Table, TableRow, TableCell
from odf.text import P
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


def get_cell_value(cell):
    """Отримати значення з комірки"""
    ps = cell.getElementsByType(P)
    text_content = ""
    for p in ps:
        text_content += str(p)
    return text_content


def parse_number(value):
    """Парсинг числа з рядка"""
    if not value or value == '0':
        return 0
    # Видаляємо коми і пробіли
    value = value.replace(',', '').replace(' ', '').strip()
    try:
        return float(value)
    except:
        return 0

def analyze_gas_subscription_fees(rows):
    """Аналізує зміни абонплати газу протягом часу"""
    subscription_periods = []
    current_fee = None
    start_date = None
    
    for i, row in enumerate(rows):
        if i < 2:  # Пропускаємо заголовки
            continue
            
        cells = row.getElementsByType(TableCell)
        if len(cells) < 10:
            continue
            
        date_str = get_cell_value(cells[0]).strip()
        if not date_str or date_str == '0' or date_str == 'Дата':
            continue
            
        try:
            date = datetime.strptime(date_str, '%d.%m.%Y')
            # Визначаємо період (віднімаємо місяць)
            period_date = date - relativedelta(months=1)
        except:
            continue
        
        # Абонплата може бути в колонці 8 або 9 залежно від періоду
        fee = None
        if date < datetime(2024, 4, 1):
            # До квітня 2024 абонплата в колонці 8
            fee_value = get_cell_value(cells[8]).strip() if len(cells) > 8 else ''
            if fee_value == '264' or fee_value == '264.00':
                fee = 264.0
        else:
            # З квітня 2024 абонплата в колонці 9
            fee = parse_number(get_cell_value(cells[9]).strip()) if len(cells) > 9 else 0
            
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


def create_tariffs(services, gas_subscription_periods):
    """Створити тарифи для всіх служб"""
    
    # Видаляємо старі тарифи для цієї адреси
    service_ids = [s.id for s in services.values()]
    db.session.query(UtilityTariff).filter(UtilityTariff.service_id.in_(service_ids)).delete()
    db.session.commit()
    logger.info("Видалено старі тарифи")
    
    tariffs = {}
    
    # Тарифи для води (змінювались з часом)
    water_tariffs_data = [
        # Водопостачання
        {'from': '2021-01-01', 'to': '2022-01-01', 'rate': 11.59, 'type': 'consumption'},
        {'from': '2022-01-01', 'to': '2022-04-01', 'rate': 12.95, 'type': 'consumption'},
        {'from': '2022-04-01', 'to': None, 'rate': 12.95, 'type': 'consumption'},
        # Водовідведення
        {'from': '2021-01-01', 'to': '2022-01-01', 'rate': 13.66, 'type': 'wastewater'},
        {'from': '2022-01-01', 'to': '2022-04-01', 'rate': 15.29, 'type': 'wastewater'},
        {'from': '2022-04-01', 'to': None, 'rate': 15.29, 'type': 'wastewater'}
    ]
    
    # Додаємо абонплату води
    water_abon_tariffs = [
        {'from': '2022-01-01', 'to': '2022-04-01', 'rate': 14.17},
        {'from': '2022-04-01', 'to': None, 'rate': 24.67}
    ]
    
    for data in water_abon_tariffs:
        water_abon_tariff = UtilityTariff(
            service_id=services['water'].id,
            name="Абонплата (вода)",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='subscription',
            group_code='water'
        )
        db.session.add(water_abon_tariff)
    
    for data in water_tariffs_data:
        tariff = UtilityTariff(
            service_id=services['water'].id,
            name=f"Вода ({'постачання' if data['type'] == 'consumption' else 'водовідведення'})",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type=data['type'],
            group_code='water'
        )
        db.session.add(tariff)
        tariffs[f"water_{data['type']}_{data['from'][:7]}"] = tariff
    
    # Тариф для газу (постійний 7.99)
    gas_tariff = UtilityTariff(
        service_id=services['gas'].id,
        name="Газ",
        rate=7.99,
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='consumption',
        group_code='gas'
    )
    db.session.add(gas_tariff)
    
    # Абонплата за газ (динамічна з періодів)
    for period in gas_subscription_periods:
        gas_subscription = UtilityTariff(
            service_id=services['gas'].id,
            name="Абонплата (газ)",
            rate=period['fee'],
            subscription_fee=0,
            currency='UAH',
            valid_from=period['from'],
            valid_to=period['to'],
            is_active=period['to'] is None,
            tariff_type='subscription',
            group_code='gas'
        )
        db.session.add(gas_subscription)
        logger.info(f"Створено абонплату газу {period['fee']} грн з {period['from'].strftime('%Y-%m-%d')}")
    
    # Тарифи для електрики
    electricity_tariff = UtilityTariff(
        service_id=services['electricity_day'].id,
        name="Денний",
        rate=4.32,
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2024-06-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='day',
        group_code='electricity'
    )
    db.session.add(electricity_tariff)
    tariffs['electricity_day'] = electricity_tariff
    
    electricity_night_tariff = UtilityTariff(
        service_id=services['electricity_night'].id,
        name="Нічний",
        rate=2.16,
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2024-06-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='night',
        group_code='electricity'
    )
    db.session.add(electricity_night_tariff)
    tariffs['electricity_night'] = electricity_night_tariff
    
    # Тариф для квартплати (змінюється)
    rent_tariff = UtilityTariff(
        service_id=services['rent'].id,
        name="Фіксований",
        rate=568.11,  # Остання актуальна ставка
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2025-01-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='fixed'
    )
    db.session.add(rent_tariff)
    
    # Тариф для сміття
    garbage_tariff = UtilityTariff(
        service_id=services['garbage'].id,
        name="Фіксований",
        rate=156.50,
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='fixed'
    )
    db.session.add(garbage_tariff)
    
    db.session.commit()
    logger.info("Створено всі тарифи")
    return tariffs

def import_readings(services, rows):
    """Імпортувати показники з ODS файлу"""
    
    # Видаляємо старі показники
    service_ids = [s.id for s in services.values()]
    db.session.query(UtilityReading).filter(
        UtilityReading.service_id.in_(service_ids),
        UtilityReading.user_id == USER_ID
    ).delete()
    db.session.commit()
    logger.info("Видалено старі показники")
    
    imported_count = 0
    
    for i, row in enumerate(rows):
        if i < 2:  # Пропускаємо заголовки
            continue
            
        cells = row.getElementsByType(TableCell)
        if len(cells) < 14:  # Мінімум потрібно 14 колонок
            continue
            
        # Парсимо дату
        date_str = get_cell_value(cells[0]).strip()
        if not date_str or date_str == '0' or date_str == 'Дата':
            continue
            
        try:
            date = datetime.strptime(date_str, '%d.%m.%Y')
            # ВАЖЛИВО: показники станом на 01.05.2025 - це дані за КВІТЕНЬ!
            period_date = date - relativedelta(months=1)
            period = period_date.strftime('%Y-%m')
        except:
            continue
        
        # Показники (беремо ПОКАЗНИКИ, а не споживання!)
        water_reading = parse_number(get_cell_value(cells[1]))
        gas_reading = parse_number(get_cell_value(cells[7]))
        electricity_day_reading = parse_number(get_cell_value(cells[11]))
        electricity_night_reading = parse_number(get_cell_value(cells[12]))
        
        # Квартплата та сміття (суми, а не показники)
        rent_amount = 0
        garbage_amount = 0
        
        if len(cells) > 14:
            rent_amount = parse_number(get_cell_value(cells[14]))
            
        if len(cells) > 16:
            garbage_amount = parse_number(get_cell_value(cells[16]))
        
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
            # Попередній показник
            if i > 0 and tariff.tariff_type not in ['subscription', 'fixed']:
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
            else:
                # Для споживання сума = споживання * тариф
                reading.amount = reading.consumption * tariff.rate if reading.consumption else 0
    
    db.session.commit()
    logger.info("✅ Розрахунки завершено")


def main():
    """Головна функція"""
    try:
        logger.info("Початок імпорту комунальних даних")
        
        # ОЧИЩАЄМО ВСІ ДАНІ ПЕРЕД ІМПОРТОМ
        logger.info("Очищення всіх попередніх даних...")
        db.session.query(UtilityReading).delete()
        db.session.query(UtilityTariff).delete()  
        db.session.query(UtilityService).delete()
        db.session.query(UtilityAddress).delete()
        db.session.commit()
        logger.info("✅ Всі дані очищено")
        
        # Завантажуємо ODS файл
        doc = opendocument.load("scripts/utility_ks6b27.ods")
        tables = doc.getElementsByType(Table)
        table = tables[0]
        rows = table.getElementsByType(TableRow)
        
        # Аналізуємо зміни абонплати газу
        logger.info("Аналіз абонплати газу...")
        gas_subscription_periods = analyze_gas_subscription_fees(rows)
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
        imported_count = import_readings(services, rows)
        
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