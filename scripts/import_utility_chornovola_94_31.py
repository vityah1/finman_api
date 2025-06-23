#!/usr/bin/env python3
"""
Скрипт імпорту комунальних показників з ODS файлу для адреси Чорновола 94/31
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
    value = value.replace(',', '').replace(' ', '').replace('.', '').strip()
    # Перетворюємо коми на крапки для десяткових
    value = value.replace(',', '.')
    try:
        return float(value)
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
    
    if 'electricity' not in services:
        electricity = UtilityService(
            user_id=USER_ID,
            address_id=address_id,
            name="Світло",
            unit="кВт·год",
            is_active=True,
            has_shared_meter=True,
            service_group="electricity"
        )
        db.session.add(electricity)
        services['electricity'] = electricity
        logger.info(f"Створено службу: Світло")    
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

def create_tariffs(services):
    """Створити тарифи для всіх служб"""
    
    # Видаляємо старі тарифи тільки для цієї адреси
    service_ids = [s.id for s in services.values()]
    db.session.query(UtilityTariff).filter(UtilityTariff.service_id.in_(service_ids)).delete()
    db.session.commit()
    logger.info("Видалено старі тарифи для цієї адреси")
    
    tariffs = {}
    
    # Тарифи для води - водопостачання (змінювались)
    water_supply_tariffs = [
        {'from': '2021-01-01', 'to': '2022-01-01', 'rate': 11.59},
        {'from': '2022-01-01', 'to': None, 'rate': 12.95}
    ]
    
    for data in water_supply_tariffs:
        tariff = UtilityTariff(
            service_id=services['water'].id,
            name="Вода (постачання)",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='consumption',
            group_code='water'
        )
        db.session.add(tariff)
    
    # Тарифи для води - водовідведення (змінювались)
    water_wastewater_tariffs = [
        {'from': '2021-01-01', 'to': '2022-01-01', 'rate': 13.66},
        {'from': '2022-01-01', 'to': None, 'rate': 15.29}
    ]
    
    for data in water_wastewater_tariffs:
        tariff = UtilityTariff(
            service_id=services['water'].id,
            name="Вода (водовідведення)",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='wastewater',
            group_code='water'
        )
        db.session.add(tariff)    
    # Абонплата за воду (змінювалась)
    water_subscription_tariffs = [
        {'from': '2022-01-01', 'to': '2022-04-01', 'rate': 14.17},
        {'from': '2022-04-01', 'to': None, 'rate': 24.67}
    ]
    
    for data in water_subscription_tariffs:
        tariff = UtilityTariff(
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
        db.session.add(tariff)
    
    # Тариф для газу (ПОСТІЙНИЙ з PDF справа)
    gas_tariff = UtilityTariff(
        service_id=services['gas'].id,
        name="Газ",
        rate=7.99,  # Постійний тариф з PDF
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='consumption',
        group_code='gas'
    )
    db.session.add(gas_tariff)
    
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
        tariff = UtilityTariff(
            service_id=services['gas'].id,
            name="Доставлення газу",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='subscription',
            group_code='gas'
        )
        db.session.add(tariff)    
    # Тарифи для електрики (змінювались кілька разів)
    electricity_tariffs = [
        {'from': '2021-01-01', 'to': '2023-06-01', 'rate': 1.44},  # До 250 кВт
        {'from': '2023-06-01', 'to': '2024-06-01', 'rate': 2.64},
        {'from': '2024-06-01', 'to': None, 'rate': 4.32}
    ]
    
    for data in electricity_tariffs:
        tariff = UtilityTariff(
            service_id=services['electricity'].id,
            name="Електроенергія",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='consumption',
            group_code='electricity'
        )
        db.session.add(tariff)
    
    # Тариф для квартплати (змінювався)
    rent_tariffs = [
        {'from': '2021-01-01', 'to': '2022-02-01', 'rate': 83.3},
        {'from': '2022-02-01', 'to': '2023-11-01', 'rate': 83.3},
        {'from': '2023-11-01', 'to': '2023-12-01', 'rate': 167.77},
        {'from': '2023-12-01', 'to': '2024-01-01', 'rate': 82.75},
        {'from': '2024-01-01', 'to': '2024-02-01', 'rate': 91.04},
        {'from': '2024-02-01', 'to': '2024-03-01', 'rate': 87.63},
        {'from': '2024-03-01', 'to': '2024-04-01', 'rate': 84.93},
        {'from': '2024-04-01', 'to': '2024-05-01', 'rate': 86.01},
        {'from': '2024-05-01', 'to': '2024-06-01', 'rate': 104.71},
        {'from': '2024-06-01', 'to': '2024-07-01', 'rate': 103.42},
        {'from': '2024-07-01', 'to': '2024-08-01', 'rate': 106.22},
        {'from': '2024-08-01', 'to': '2024-09-01', 'rate': 104.2},
        {'from': '2024-09-01', 'to': '2024-10-01', 'rate': 104.24},
        {'from': '2024-10-01', 'to': '2024-11-01', 'rate': 107.18},
        {'from': '2024-11-01', 'to': '2024-12-01', 'rate': 105.92},
        {'from': '2024-12-01', 'to': '2025-01-01', 'rate': 106.9},
        {'from': '2025-01-01', 'to': '2025-02-01', 'rate': 107.31},
        {'from': '2025-02-01', 'to': '2025-03-01', 'rate': 107.06},
        {'from': '2025-03-01', 'to': '2025-04-01', 'rate': 135},
        {'from': '2025-04-01', 'to': None, 'rate': 124.03}
    ]
    
    for data in rent_tariffs:
        tariff = UtilityTariff(
            service_id=services['rent'].id,
            name="Фіксований",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='fixed'
        )
        db.session.add(tariff)
    
    # Тарифи для сміття - змінювались
    garbage_tariffs = [
        {'from': '2021-11-01', 'to': '2021-12-01', 'rate': 0},
        {'from': '2021-12-01', 'to': '2022-09-01', 'rate': 22.54},
        {'from': '2022-09-01', 'to': '2022-10-01', 'rate': 107.28},  # компенсація
        {'from': '2022-10-01', 'to': None, 'rate': 37.2}
    ]
    
    for data in garbage_tariffs:
        tariff = UtilityTariff(
            service_id=services['garbage'].id,
            name="Фіксований",
            rate=data['rate'],
            subscription_fee=0,
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,
            tariff_type='fixed',
            group_code='garbage'
        )
        db.session.add(tariff)
    
    db.session.commit()
    logger.info("Створено всі тарифи")
    return tariffs

def import_readings(services, rows):
    """Імпортувати показники з ODS файлу"""
    
    # Видаляємо старі показники тільки для цієї адреси
    service_ids = [s.id for s in services.values()]
    db.session.query(UtilityReading).filter(
        UtilityReading.service_id.in_(service_ids),
        UtilityReading.user_id == USER_ID
    ).delete()
    db.session.commit()
    logger.info("Видалено старі показники для цієї адреси")
    
    imported_count = 0
    processed_periods = set()  # Для відстеження вже оброблених періодів
    
    for i, row in enumerate(rows):
        if i < 3:  # Пропускаємо заголовки (у PDF 3 рядки заголовків)
            continue
            
        cells = row.getElementsByType(TableCell)
        if len(cells) < 17:  # Мінімум потрібно 17 колонок
            continue
            
        # Парсимо дату
        date_str = get_cell_value(cells[0]).strip()
        if not date_str or date_str == '0' or date_str == 'Дата' or not date_str.startswith('01.'):
            continue
            
        try:
            date = datetime.strptime(date_str, '%d.%m.%Y')
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
        # Показники (правильні колонки з ODS)
        water_reading = parse_number(get_cell_value(cells[1]))      # B: показник води
        water_consumption = parse_number(get_cell_value(cells[2]))   # C: споживання води
        water_abon = parse_number(get_cell_value(cells[3]))         # D: абонплата води
        water_amount = parse_number(get_cell_value(cells[4]))       # E: сума за воду
        gas_reading = parse_number(get_cell_value(cells[6]))        # G: показник газу
        gas_consumption = parse_number(get_cell_value(cells[7]))    # H: споживання газу
        gas_delivery = parse_number(get_cell_value(cells[8]))       # I: доставлення (АБОНПЛАТА)
        gas_amount = parse_number(get_cell_value(cells[9]))         # J: сума за споживання
        rent_amount = parse_number(get_cell_value(cells[11]))       # L: квартплата
        garbage_amount = parse_number(get_cell_value(cells[13]))    # N: сміття
        electricity_reading = parse_number(get_cell_value(cells[15])) # P: показник світла
        
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
                
                # Для абонплати води з березня 2024 використовуємо значення з колонки D
                if tariff.tariff_type == 'subscription' and water_abon > 0:
                    amount = water_abon
                else:
                    amount = None
                
                reading = UtilityReading(
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
        
        # Створюємо показники для електрики (єдиний тариф)
        if electricity_reading > 0:
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['electricity'].id,
                UtilityTariff.is_active == True
            ).first()
            
            if tariff:
                reading = UtilityReading(
                    user_id=USER_ID,
                    address_id=services['electricity'].address_id,
                    service_id=services['electricity'].id,
                    tariff_id=tariff.id,
                    period=period,
                    current_reading=electricity_reading,
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
        if garbage_amount >= 0:  # Включаємо і 0
            tariff = db.session.query(UtilityTariff).filter(
                UtilityTariff.service_id == services['garbage'].id,
                UtilityTariff.valid_from <= date,
                or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
            ).first()
            
            if tariff:
                reading = UtilityReading(
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
        logger.info("Початок імпорту комунальних даних для адреси Чорновола 94/31")
        
        # Завантажуємо ODS файл
        doc = opendocument.load("scripts/utility_chornovola_94_31.ods")
        tables = doc.getElementsByType(Table)
        table = tables[0]
        rows = table.getElementsByType(TableRow)
        
        # Створюємо адресу
        address = create_or_get_address()
        
        # Створюємо служби
        logger.info("Створення служб...")
        services = create_services(address.id)
        
        # Створюємо тарифи
        logger.info("Створення тарифів...")
        create_tariffs(services)
        
        # Імпортуємо показники
        logger.info("Імпорт показників...")
        imported_count = import_readings(services, rows)
        
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