#!/usr/bin/env python3
"""
Скрипт імпорту комунальних показників з ODS файлу для адреси Карпатської Січі 6Б/27
"""

import sys
import os
from datetime import datetime, timezone
import logging
import traceback

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from models.models import UtilityAddress, UtilityService, UtilityTariff, UtilityReading
from mydb import db

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_ID = 1
ADDRESS_NAME = "Карпатська Січі 6Б/27"
ADDRESS_FULL = "м. Івано-Франківськ, вул. Карпатської Січі 6Б, кв. 27"


def calculate_electricity_costs():
    """Розраховує споживання та вартість для електроенергії з 2025"""
    logger.info("Розрахунок споживання та вартості електроенергії...")

    # Знаходимо всі записи електроенергії з 2025 (день і ніч)
    day_readings = db.session.query(UtilityReading).filter(
        UtilityReading.user_id == USER_ID,
        UtilityReading.period >= '2025-01'
    ).join(UtilityService).filter(
        UtilityService.name == 'Електроенергія (день)'
    ).order_by(UtilityReading.period).all()

    night_readings = db.session.query(UtilityReading).filter(
        UtilityReading.user_id == USER_ID,
        UtilityReading.period >= '2025-01'
    ).join(UtilityService).filter(
        UtilityService.name == 'Електроенергія (ніч)'
    ).order_by(UtilityReading.period).all()

    # Розраховуємо для денних показників
    prev_day_reading = None
    for reading in day_readings:
        if prev_day_reading:
            consumption = reading.current_reading - prev_day_reading.current_reading
            reading.previous_reading = prev_day_reading.current_reading
            reading.consumption = consumption

            # Розраховуємо вартість
            tariff = db.session.get(UtilityTariff, reading.tariff_id)
            if tariff and consumption > 0:
                reading.amount = consumption * tariff.rate
                logger.info(f"Розраховано день {reading.period}: споживання={consumption}, тариф={tariff.rate}, сума={reading.amount}")
        
        prev_day_reading = reading

    # Розраховуємо для нічних показників
    prev_night_reading = None
    for reading in night_readings:
        if prev_night_reading:
            consumption = reading.current_reading - prev_night_reading.current_reading
            reading.previous_reading = prev_night_reading.current_reading
            reading.consumption = consumption

            # Розраховуємо вартість
            tariff = db.session.get(UtilityTariff, reading.tariff_id)
            if tariff and consumption > 0:
                reading.amount = consumption * tariff.rate
                logger.info(f"Розраховано ніч {reading.period}: споживання={consumption}, тариф={tariff.rate}, сума={reading.amount}")
        
        prev_night_reading = reading

    db.session.commit()
    logger.info("Розрахунок електроенергії завершено")


def get_tariff_for_period(tariffs_dict, period):
    """Отримує тариф для конкретного періоду"""
    period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
    
    # Знаходимо найближчий тариф, що діє для цього періоду
    applicable_tariff = None
    for tariff_period, tariff in tariffs_dict.items():
        tariff_date = datetime.strptime(tariff_period + "-01", "%Y-%m-%d").date()
        if tariff_date <= period_date:
            if applicable_tariff is None or tariff_date > datetime.strptime(applicable_tariff[0] + "-01", "%Y-%m-%d").date():
                applicable_tariff = (tariff_period, tariff)
    
    return applicable_tariff[1] if applicable_tariff else None


def get_or_create_gas_tariff(service_id, period, subscription_fee):
    """Створює або знаходить тариф газу з правильною абонплатою"""
    # Тепер не створюємо нові тарифи, а використовуємо існуючі
    # Це функція залишена для сумісності, але логіку змінено
    return None


def read_tariffs_from_file(table):
    """Зчитує тарифи з таблиці файлу"""
    rows = table.getElementsByType(TableRow)
    tariff_data = {
        "water_supply": [],
        "water_drainage": [],
        "water_subscription": []
    }
    
    # Виводимо колонки U, V, W, X для діагностики (колонки 20-23)
    logger.info("Діагностика колонок U, V, W, X:")
    for row_idx in range(min(20, len(rows))):
        row = rows[row_idx]
        cells = row.getElementsByType(TableCell)
        if len(cells) >= 24:
            cell_values = []
            for col_idx in [20, 21, 22, 23]:  # U, V, W, X
                if col_idx < len(cells):
                    cell_values.append(get_cell_value(cells[col_idx]))
                else:
                    cell_values.append(None)
            logger.info(f"Рядок {row_idx + 1} (U,V,W,X): {cell_values}")
    
    # Шукаємо таблицю тарифів у правій частині файлу (колонки U, V, W, X = 20, 21, 22, 23)
    for row_idx in range(len(rows)):
        row = rows[row_idx]
        cells = row.getElementsByType(TableCell)
        
        # Перевіряємо чи є достатньо колонок
        if len(cells) >= 24:
            cell_u = get_cell_value(cells[20]) if len(cells) > 20 else ""  # Колонка U
            cell_v = get_cell_value(cells[21]) if len(cells) > 21 else ""  # Колонка V
            cell_w = get_cell_value(cells[22]) if len(cells) > 22 else ""  # Колонка W
            cell_x = get_cell_value(cells[23]) if len(cells) > 23 else ""  # Колонка X
            
            # Знаходимо заголовок таблиці тарифів
            if (cell_u and "дата" in cell_u.lower() and 
                cell_v and ("водовідведення" in cell_v.lower() or "канал" in cell_v.lower()) and
                cell_w and "водопостачання" in cell_w.lower() and
                cell_x and "абон" in cell_x.lower()):
                
                logger.info(f"Знайдено таблицю тарифів в рядку {row_idx + 1}: U='{cell_u}', V='{cell_v}', W='{cell_w}', X='{cell_x}'")
                
                # Читаємо наступні рядки з тарифами
                for next_row_idx in range(row_idx + 1, min(row_idx + 10, len(rows))):
                    next_row = rows[next_row_idx]
                    next_cells = next_row.getElementsByType(TableCell)
                    
                    if len(next_cells) >= 24:
                        date_str = get_cell_value(next_cells[20])
                        drainage_rate = convert_to_float(get_cell_value(next_cells[21]))
                        supply_rate = convert_to_float(get_cell_value(next_cells[22]))
                        subscription_fee = convert_to_float(get_cell_value(next_cells[23]))
                        
                        logger.info(f"Рядок {next_row_idx + 1}: дата='{date_str}', водовідв={drainage_rate}, водопост={supply_rate}, абонпл={subscription_fee}")
                        
                        if date_str and drainage_rate is not None and supply_rate is not None:
                            try:
                                tariff_date = parse_date(date_str)
                                if tariff_date:
                                    period = tariff_date.strftime('%Y-%m')
                                    
                                    tariff_data["water_supply"].append({
                                        "period": period,
                                        "rate": supply_rate,
                                        "subscription": subscription_fee if subscription_fee else 0.0,
                                        "date": tariff_date
                                    })
                                    
                                    tariff_data["water_drainage"].append({
                                        "period": period,
                                        "rate": drainage_rate,
                                        "date": tariff_date
                                    })
                                    
                                    logger.info(f"Зчитано тариф {period}: водопостачання={supply_rate}, водовідведення={drainage_rate}, абонплата={subscription_fee}")
                                    
                            except Exception as e:
                                logger.warning(f"Помилка парсингу тарифу в рядку {next_row_idx + 1}: {e}")
                        else:
                            # Якщо в рядку немає дати або тарифів - закінчуємо читання
                            if not date_str:
                                break
                break
    
    logger.info(f"Зчитано тарифів: водопостачання={len(tariff_data['water_supply'])}, водовідведення={len(tariff_data['water_drainage'])}")
    return tariff_data


def create_tariffs(services, file_tariff_data):
    """Створює базові тарифи з урахуванням даних з файлу"""
    tariffs = {}

    # Якщо тарифи не знайдені у файлі, використовуємо дефолтні значення
    if len(file_tariff_data["water_supply"]) == 0:
        logger.warning("Тарифи не знайдені у файлі, використовуємо дефолтні значення")
        file_tariff_data["water_supply"] = [
            {"period": "2021-08", "rate": 11.59, "subscription": 0.0, "date": datetime(2021, 8, 1).date()},
            {"period": "2022-01", "rate": 12.95, "subscription": 14.17, "date": datetime(2022, 1, 1).date()},
            {"period": "2022-04", "rate": 12.95, "subscription": 24.67, "date": datetime(2022, 4, 1).date()},
        ]
        file_tariff_data["water_drainage"] = [
            {"period": "2021-08", "rate": 13.66, "date": datetime(2021, 8, 1).date()},
            {"period": "2022-01", "rate": 15.29, "date": datetime(2022, 1, 1).date()},
            {"period": "2022-04", "rate": 15.29, "date": datetime(2022, 4, 1).date()},
        ]

    # Створюємо тарифи водопостачання з даних файлу
    tariffs["Водопостачання"] = {}
    for i, tariff_info in enumerate(file_tariff_data["water_supply"]):
        is_active = i == len(file_tariff_data["water_supply"]) - 1  # Останній тариф активний
        tariff = UtilityTariff(
            service_id=services["Водопостачання"].id,
            name=f"Водопостачання-{tariff_info['period']}",
            rate=tariff_info["rate"],
            subscription_fee=tariff_info["subscription"],
            currency="UAH",
            valid_from=datetime.combine(tariff_info["date"], datetime.min.time()).replace(tzinfo=timezone.utc),
            is_active=is_active,
            tariff_type="consumption",
            group_code=f"water_{tariff_info['period']}",
            calculation_method="standard"
        )
        db.session.add(tariff)
        db.session.flush()
        tariffs["Водопостачання"][tariff_info["period"]] = tariff
        logger.info(f"Створено тариф: {tariff.name} - {tariff.rate} грн/м³, абонплата: {tariff.subscription_fee}")

    # Створюємо тарифи водовідведення з даних файлу
    tariffs["Водовідведення"] = {}
    for i, tariff_info in enumerate(file_tariff_data["water_drainage"]):
        is_active = i == len(file_tariff_data["water_drainage"]) - 1  # Останній тариф активний
        # Знаходимо відповідний період для водопостачання
        water_supply_period = tariff_info["period"]
        
        tariff = UtilityTariff(
            service_id=services["Водопостачання"].id,
            name=f"Водовідведення-{tariff_info['period']}",
            rate=tariff_info["rate"],
            subscription_fee=0.0,  # Водовідведення БЕЗ абонплати
            currency="UAH",
            valid_from=datetime.combine(tariff_info["date"], datetime.min.time()).replace(tzinfo=timezone.utc),
            is_active=is_active,
            tariff_type="drainage",
            group_code=f"water_{tariff_info['period']}",
            calculation_method="standard"
        )
        db.session.add(tariff)
        db.session.flush()
        tariffs["Водовідведення"][tariff_info["period"]] = tariff
        logger.info(f"Створено тариф: {tariff.name} - {tariff.rate} грн/м³")

    # Тарифи для газу з різними абонплатами (статичні дані)
    gas_tariffs = [
        {"period": "2021-08", "subscription": 264.0, "valid_from": datetime(2021, 8, 1, tzinfo=timezone.utc), "active": False},
        {"period": "2024-11", "subscription": 209.01, "valid_from": datetime(2024, 11, 1, tzinfo=timezone.utc), "active": False},
        {"period": "2025-02", "subscription": 147.5, "valid_from": datetime(2025, 2, 1, tzinfo=timezone.utc), "active": True},
    ]

    # Створюємо тарифи газу
    tariffs["Газопостачання"] = {}
    for tariff_data in gas_tariffs:
        tariff = UtilityTariff(
            service_id=services["Газопостачання"].id,
            name=f"Газ-{tariff_data['period']}",
            rate=7.99,  # З файлу
            subscription_fee=tariff_data["subscription"],
            currency="UAH",
            valid_from=tariff_data["valid_from"],
            is_active=tariff_data["active"]
        )
        db.session.add(tariff)
        db.session.flush()
        tariffs["Газопостачання"][tariff_data["period"]] = tariff
        logger.info(f"Створено тариф: {tariff.name} - {tariff.rate} грн/м³, абонплата: {tariff.subscription_fee}")

    # Тарифи електроенергії
    # До 2025 - загальний тариф
    electricity_general = UtilityTariff(
        service_id=services["Електроенергія"].id,
        name="Загальний",
        rate=0.0,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2021, 8, 1, tzinfo=timezone.utc),
        is_active=False
    )
    db.session.add(electricity_general)
    db.session.flush()
    
    # З 2025 - денний тариф
    electricity_day = UtilityTariff(
        service_id=services["Електроенергія (день)"].id,
        name="Денний",
        rate=4.32,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        is_active=True
    )
    db.session.add(electricity_day)
    db.session.flush()

    # З 2025 - нічний тариф
    electricity_night = UtilityTariff(
        service_id=services["Електроенергія (ніч)"].id,
        name="Нічний", 
        rate=2.16,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        is_active=True
    )
    db.session.add(electricity_night)
    db.session.flush()

    tariffs["Електроенергія"] = {"Загальний": electricity_general}
    tariffs["Електроенергія (день)"] = {"Денний": electricity_day}
    tariffs["Електроенергія (ніч)"] = {"Нічний": electricity_night}

    # Тариф квартплати
    apartment_tariff = UtilityTariff(
        service_id=services["Квартплата"].id,
        name="Фіксований",
        rate=0.0,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2021, 8, 1, tzinfo=timezone.utc),
        is_active=True
    )
    db.session.add(apartment_tariff)
    db.session.flush()

    # Тариф сміття
    waste_tariff = UtilityTariff(
        service_id=services["Вивіз сміття"].id,
        name="Фіксований",
        rate=0.0,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2021, 8, 1, tzinfo=timezone.utc),
        is_active=True
    )
    db.session.add(waste_tariff)
    db.session.flush()

    tariffs["Квартплата"] = {"Фіксований": apartment_tariff}
    tariffs["Вивіз сміття"] = {"Фіксований": waste_tariff}

    logger.info("Створено тарифи для всіх служб")
    return tariffs


def get_cell_value(cell):
    """Отримує текстове значення з комірки ODS"""
    paragraphs = cell.getElementsByType(P)
    cell_text = ''
    for p in paragraphs:
        if p.firstChild:
            cell_text += str(p.firstChild)
    return cell_text.strip() if cell_text else None

def convert_to_float(value):
    """Конвертує значення в float"""
    if not value:
        return None
    try:
        value_str = str(value).replace(',', '.')
        return float(value_str)
    except (ValueError, TypeError):
        return None

def parse_date(date_str):
    """Парсить дату"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        try:
            if isinstance(date_str, str):
                date_obj = datetime.fromisoformat(date_str.replace('T', ' ').replace('Z', ''))
                return date_obj.date()
            else:
                if hasattr(date_str, 'date'):
                    return date_str.date()
                return date_str
        except (ValueError, AttributeError):
            return None
def cleanup_existing_data():
    """Очищує існуючі дані"""
    logger.info("Очищення існуючих даних...")
    
    address = db.session.query(UtilityAddress).filter_by(user_id=USER_ID, name=ADDRESS_NAME).first()
    if address:
        readings_count = db.session.query(UtilityReading).filter_by(user_id=USER_ID, address_id=address.id).count()
        if readings_count > 0:
            db.session.query(UtilityReading).filter_by(user_id=USER_ID, address_id=address.id).delete()
            db.session.commit()
        
        services = db.session.query(UtilityService).filter_by(user_id=USER_ID, address_id=address.id).all()
        tariffs_count = 0
        for service in services:
            tariffs = db.session.query(UtilityTariff).filter_by(service_id=service.id).count()
            tariffs_count += tariffs
            if tariffs > 0:
                db.session.query(UtilityTariff).filter_by(service_id=service.id).delete()
        db.session.commit()
        
        services_count = len(services)
        if services_count > 0:
            db.session.query(UtilityService).filter_by(user_id=USER_ID, address_id=address.id).delete()
            db.session.commit()
        
        db.session.delete(address)
        db.session.commit()
        
        logger.info(f"Видалено: {readings_count} показників, {tariffs_count} тарифів, {services_count} служб, 1 адресу")
    else:
        logger.info("Попередніх даних не знайдено")

def create_address():
    """Створює адресу"""
    address = db.session.query(UtilityAddress).filter_by(user_id=USER_ID, name=ADDRESS_NAME).first()
    if not address:
        address = UtilityAddress(
            user_id=USER_ID,
            name=ADDRESS_NAME,
            address=ADDRESS_FULL,
            description="Основна квартира",
            is_active=True
        )
        db.session.add(address)
        db.session.flush()
        logger.info(f"Створено адресу: {ADDRESS_NAME}")
    return address

def create_services(address_id):
    """Створює комунальні служби"""
    services = {}
    service_configs = [
        {"name": "Водопостачання", "unit": "м³", "meter_number": None, "has_shared_meter": True},
        {"name": "Газопостачання", "unit": "м³", "meter_number": None, "has_shared_meter": False},
        {"name": "Електроенергія (день)", "unit": "кВт·год", "meter_number": None, "has_shared_meter": False},
        {"name": "Електроенергія (ніч)", "unit": "кВт·год", "meter_number": None, "has_shared_meter": False},
        {"name": "Електроенергія", "unit": "кВт·год", "meter_number": None, "has_shared_meter": False},  # До 2025
        {"name": "Квартплата", "unit": "міс", "meter_number": None, "has_shared_meter": False},
        {"name": "Вивіз сміття", "unit": "міс", "meter_number": None, "has_shared_meter": False}
    ]
    
    for config in service_configs:
        service = db.session.query(UtilityService).filter_by(
            user_id=USER_ID, address_id=address_id, name=config["name"]
        ).first()
        if not service:
            service = UtilityService(
                user_id=USER_ID, address_id=address_id, name=config["name"],
                unit=config["unit"], meter_number=config["meter_number"], 
                has_shared_meter=config["has_shared_meter"], is_active=True
            )
            db.session.add(service)
            db.session.flush()
            logger.info(f"Створено службу: {config['name']} (спільний показник: {config['has_shared_meter']})")
        services[config["name"]] = service
    return services

def import_utility_data(file_path):
    """Основна функція імпорту"""
    logger.info(f"Починаємо імпорт з файлу: {file_path}")
    
    try:
        cleanup_existing_data()
        
        doc = load(file_path)
        tables = doc.getElementsByType(Table)
        if not tables:
            logger.error("Не знайдено жодної таблиці в файлі")
            return False
        
        table = tables[0]
        rows = table.getElementsByType(TableRow)
        
        address = create_address()
        services = create_services(address.id)
        
        # Зчитуємо тарифи з файлу
        file_tariff_data = read_tariffs_from_file(table)
        tariffs = create_tariffs(services, file_tariff_data)
        
        imported_count = 0
        
        for row_idx in range(4, len(rows)):  # З 5 рядка
            row = rows[row_idx]
            cells = row.getElementsByType(TableCell)
            
            if len(cells) < 15:
                logger.warning(f"Пропускаємо рядок {row_idx + 1}: недостатньо колонок ({len(cells)})")
                continue
            
            date_str = get_cell_value(cells[0])
            reading_date = parse_date(date_str)
            if not reading_date:
                logger.warning(f"Пропускаємо рядок {row_idx + 1}: некоректна дата {date_str}")
                continue
            
            period = reading_date.strftime('%Y-%m')
            # Якщо день = 1, то це показники за попередній місяць
            if reading_date.day == 1:
                if reading_date.month == 1:
                    period = f"{reading_date.year - 1}-12"
                else:
                    period = f"{reading_date.year}-{reading_date.month - 1:02d}"
            
            water_reading = convert_to_float(get_cell_value(cells[1]))
            water_consumption = convert_to_float(get_cell_value(cells[2]))
            water_amount = convert_to_float(get_cell_value(cells[3]))
            
            gas_reading = convert_to_float(get_cell_value(cells[7]))
            gas_consumption = convert_to_float(get_cell_value(cells[8]))
            gas_amount = convert_to_float(get_cell_value(cells[10]))
            
            if reading_date < datetime(2025, 1, 1).date():
                electricity_amount = convert_to_float(get_cell_value(cells[13]))
                electricity_day = None
                electricity_night = None
            else:
                electricity_day = convert_to_float(get_cell_value(cells[11]))
                electricity_night = convert_to_float(get_cell_value(cells[12]))
                electricity_amount = None
            
            payment_date_str = get_cell_value(cells[18]) if len(cells) > 18 else None
            payment_amount = convert_to_float(get_cell_value(cells[19])) if len(cells) > 19 else None
            is_paid = bool(payment_date_str or payment_amount) if payment_date_str or payment_amount else True
            
            apartment_fee = convert_to_float(get_cell_value(cells[14])) if len(cells) > 14 else None
            waste_fee = convert_to_float(get_cell_value(cells[16])) if len(cells) > 16 else None
            
            if water_reading is not None:
                # Водопостачання - знаходимо правильні тарифи для періоду
                water_supply_tariff = get_tariff_for_period(tariffs["Водопостачання"], period)
                water_drainage_tariff = get_tariff_for_period(tariffs["Водовідведення"], period)
                
                if water_supply_tariff:
                    # Рахуємо суму за водопостачання + абонплата вже в тарифі
                    water_supply_amount = (water_consumption * water_supply_tariff.rate + water_supply_tariff.subscription_fee) if water_consumption else water_supply_tariff.subscription_fee
                    import_water_reading(address.id, services["Водопостачання"].id, water_supply_tariff.id, period, 
                                       water_reading, water_consumption, water_supply_amount, reading_date, is_paid, "Водопостачання")
                    imported_count += 1
                
                if water_drainage_tariff:
                    # Рахуємо суму за водовідведення (без абонплати)
                    water_drainage_amount = water_consumption * water_drainage_tariff.rate if water_consumption else None
                    import_water_reading(address.id, services["Водопостачання"].id, water_drainage_tariff.id, period, 
                                       water_reading, water_consumption, water_drainage_amount, reading_date, is_paid, "Водовідведення")
                    imported_count += 1
            
            if gas_reading is not None:
                # Газ - знаходимо правильний тариф для періоду
                gas_tariff = get_tariff_for_period(tariffs["Газопостачання"], period)
                if gas_tariff:
                    import_gas_reading(address.id, services["Газопостачання"].id, gas_tariff.id, period,
                                     gas_reading, gas_consumption, gas_amount, reading_date, is_paid)
                    imported_count += 1
            
            # Імпорт електроенергії
            if reading_date < datetime(2025, 1, 1).date():
                # До 2025 - тільки сума до оплати
                if electricity_amount is not None:
                    import_electricity_reading(address.id, services["Електроенергія"].id, tariffs["Електроенергія"]["Загальний"].id, period,
                                              0, None, electricity_amount, reading_date, is_paid, "Сума до оплати")
                    imported_count += 1
            else:
                # З 2025 - показники день і ніч з розрахунком вартості
                day_tariff = tariffs["Електроенергія (день)"]["Денний"]
                night_tariff = tariffs["Електроенергія (ніч)"]["Нічний"]
                
                # Шукаємо попередні показники для розрахунку споживання
                prev_period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
                if prev_period_date.month == 1:
                    prev_period = f"{prev_period_date.year - 1}-12"
                else:
                    prev_period = f"{prev_period_date.year}-{prev_period_date.month - 1:02d}"
                
                prev_day_reading = db.session.query(UtilityReading).filter_by(
                    user_id=USER_ID, address_id=address.id, service_id=services["Електроенергія (день)"].id, period=prev_period
                ).first()
                
                prev_night_reading = db.session.query(UtilityReading).filter_by(
                    user_id=USER_ID, address_id=address.id, service_id=services["Електроенергія (ніч)"].id, period=prev_period
                ).first()
                
                if electricity_day is not None:
                    day_amount = None
                    day_consumption = None
                    
                    if prev_day_reading:
                        # Є попередній показник - рахуємо споживання і вартість
                        day_consumption = electricity_day - prev_day_reading.current_reading
                        day_amount = day_consumption * day_tariff.rate
                    elif electricity_amount is not None:
                        # Немає попереднього показника, але є сума - ставимо всю суму на день
                        day_amount = electricity_amount
                    
                    import_electricity_reading(address.id, services["Електроенергія (день)"].id, day_tariff.id, period,
                                              electricity_day, day_consumption, day_amount, reading_date, is_paid, "Денний тариф")
                    imported_count += 1
                
                if electricity_night is not None:
                    night_amount = None
                    night_consumption = None
                    
                    if prev_night_reading:
                        # Є попередній показник - рахуємо споживання і вартість
                        night_consumption = electricity_night - prev_night_reading.current_reading
                        night_amount = night_consumption * night_tariff.rate
                    # Якщо немає попереднього показника і немає суми - залишаємо None
                    
                    import_electricity_reading(address.id, services["Електроенергія (ніч)"].id, night_tariff.id, period,
                                              electricity_night, night_consumption, night_amount, reading_date, is_paid, "Нічний тариф")
                    imported_count += 1
            
            # Імпорт квартплати
            if apartment_fee is not None:
                import_other_reading(address.id, services["Квартплата"].id, tariffs["Квартплата"]["Фіксований"].id, period,
                                   apartment_fee, reading_date, is_paid, "Квартплата")
                imported_count += 1
            
            # Імпорт сміття
            if waste_fee is not None:
                import_other_reading(address.id, services["Вивіз сміття"].id, tariffs["Вивіз сміття"]["Фіксований"].id, period,
                                   waste_fee, reading_date, is_paid, "Вивіз сміття")
                imported_count += 1
        
        db.session.commit()
        logger.info(f"Імпорт завершено успішно. Оброблено {imported_count} записів.")
        
        # Розраховуємо споживання та вартість електроенергії
        calculate_electricity_costs()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Помилка під час імпорту: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def import_water_reading(address_id, service_id, tariff_id, period, current_reading, consumption, amount, reading_date, is_paid, notes=None):
    """Імпортує показник води"""
    existing = db.session.query(UtilityReading).filter_by(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period, tariff_id=tariff_id
    ).first()
    if existing:
        logger.info(f"Показник води ({notes}) за {period} вже існує")
        return
    
    reading = UtilityReading(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period,
        current_reading=current_reading, consumption=consumption, tariff_id=tariff_id,
        amount=amount, reading_date=datetime.combine(reading_date, datetime.min.time()).replace(tzinfo=timezone.utc),
        is_paid=is_paid, notes=notes
    )
    db.session.add(reading)
    logger.info(f"Додано показник води ({notes}): {period} - показник:{current_reading}, спожито:{consumption}, сума:{amount}")

def import_gas_reading(address_id, service_id, tariff_id, period, current_reading, consumption, amount, reading_date, is_paid):
    """Імпортує показник газу"""
    existing = db.session.query(UtilityReading).filter_by(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period
    ).first()
    if existing:
        logger.info(f"Показник газу за {period} вже існує")
        return
    
    reading = UtilityReading(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period,
        current_reading=current_reading, consumption=consumption, tariff_id=tariff_id,
        amount=amount, reading_date=datetime.combine(reading_date, datetime.min.time()).replace(tzinfo=timezone.utc),
        is_paid=is_paid
    )
    db.session.add(reading)
    logger.info(f"Додано показник газу: {period} - показник:{current_reading}, спожито:{consumption}, сума:{amount}, оплачено:{is_paid}")

def import_electricity_reading(address_id, service_id, tariff_id, period, current_reading, consumption, amount, reading_date, is_paid, notes):
    """Імпортує показник електроенергії"""
    # Для періодів з 2025 року може бути кілька записів (день/ніч), тому перевіряємо по tariff_id
    existing = db.session.query(UtilityReading).filter_by(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period, tariff_id=tariff_id
    ).first()
    if existing:
        logger.info(f"Показник електроенергії за {period} (тариф {tariff_id}) вже існує")
        return
    
    reading = UtilityReading(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period,
        current_reading=current_reading, consumption=consumption, tariff_id=tariff_id,
        amount=amount, reading_date=datetime.combine(reading_date, datetime.min.time()).replace(tzinfo=timezone.utc),
        is_paid=is_paid, notes=notes
    )
    db.session.add(reading)
    logger.info(f"Додано показник електроенергії: {period} - показник:{current_reading}, сума:{amount}, оплачено:{is_paid} ({notes})")

def import_other_reading(address_id, service_id, tariff_id, period, amount, reading_date, is_paid, notes):
    """Імпортує інші показники (квартплата, сміття)"""
    existing = db.session.query(UtilityReading).filter_by(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period, tariff_id=tariff_id
    ).first()
    if existing:
        logger.info(f"Показник {notes} за {period} вже існує")
        return
    
    reading = UtilityReading(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period,
        current_reading=0, consumption=None, tariff_id=tariff_id,
        amount=amount, reading_date=datetime.combine(reading_date, datetime.min.time()).replace(tzinfo=timezone.utc),
        is_paid=is_paid, notes=notes
    )
    db.session.add(reading)
    logger.info(f"Додано {notes}: {period} - сума:{amount}, оплачено:{is_paid}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Використання: python import_utility_ks6b27.py <шлях_до_ods_файлу>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Файл не знайдено: {file_path}")
        sys.exit(1)
    
    try:
        success = import_utility_data(file_path)
        if success:
            print("Імпорт завершено успішно!")
        else:
            print("Імпорт завершено з помилками!")
            sys.exit(1)
    except Exception as e:
        print(f"Критична помилка: {e}")
        sys.exit(1)
