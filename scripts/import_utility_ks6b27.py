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

    # Знаходимо всі записи електроенергії з 2025
    electricity_readings = db.session.query(UtilityReading).filter(
        UtilityReading.user_id == USER_ID,
        UtilityReading.period >= '2025-01'
    ).join(UtilityService).filter(
        UtilityService.name == 'Електроенергія'
    ).order_by(UtilityReading.period, UtilityReading.tariff_id).all()

    for reading in electricity_readings:
        # Знаходимо попередній період
        year, month = map(int, reading.period.split('-'))
        if month == 1:
            prev_period = f"{year - 1}-12"
        else:
            prev_period = f"{year}-{month - 1:02d}"

        # Шукаємо попередній показник з тим же тарифом
        prev_reading = db.session.query(UtilityReading).filter(
            UtilityReading.user_id == USER_ID,
            UtilityReading.address_id == reading.address_id,
            UtilityReading.service_id == reading.service_id,
            UtilityReading.period == prev_period,
            UtilityReading.tariff_id == reading.tariff_id
        ).first()

        if prev_reading:
            # Розраховуємо споживання
            consumption = reading.current_reading - prev_reading.current_reading
            reading.previous_reading = prev_reading.current_reading
            reading.consumption = consumption

            # Розраховуємо вартість
            tariff = db.session.get(UtilityTariff, reading.tariff_id)
            if tariff:
                reading.amount = consumption * tariff.rate
                logger.info(
                    f"Розраховано для {reading.period} ({reading.notes}): споживання={consumption}, тариф={tariff.rate}, сума={reading.amount}"
                )

    db.session.commit()
    logger.info("Розрахунок завершено")


def create_tariffs(services):
    """Створює базові тарифи"""
    tariffs = {}

    # Тариф для води
    water_tariff = UtilityTariff(
        service_id=services["Водопостачання"].id,
        name="Базовий",
        rate=12.95,
        subscription_fee=24.67,
        currency="UAH",
        valid_from=datetime(2021, 8, 1, tzinfo=timezone.utc),
        is_active=True
    )

    # Тариф для газу
    gas_tariff = UtilityTariff(
        service_id=services["Газопостачання"].id,
        name="Стандартний",
        rate=7.99,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2021, 8, 1, tzinfo=timezone.utc),
        is_active=True
    )

    # Тариф електроенергії загальний (до 2025)
    electricity_general = UtilityTariff(
        service_id=services["Електроенергія"].id,
        name="Загальний",
        rate=0.0,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2021, 8, 1, tzinfo=timezone.utc),
        is_active=True
    )

    # Тариф електроенергії день (з 2025)
    electricity_day = UtilityTariff(
        service_id=services["Електроенергія"].id,
        name="Денний",
        rate=4.32,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        is_active=True
    )

    # Тариф електроенергії ніч (з 2025)
    electricity_night = UtilityTariff(
        service_id=services["Електроенергія"].id,
        name="Нічний",
        rate=2.16,
        subscription_fee=0.0,
        currency="UAH",
        valid_from=datetime(2025, 1, 1, tzinfo=timezone.utc),
        is_active=True
    )

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

    all_tariffs = [water_tariff, gas_tariff, electricity_general, electricity_day,
                   electricity_night, apartment_tariff, waste_tariff]

    for tariff in all_tariffs:
        existing = db.session.query(UtilityTariff).filter_by(
            service_id=tariff.service_id, name=tariff.name
        ).first()
        if not existing:
            db.session.add(tariff)
            db.session.flush()
            logger.info(
                f"Створено тариф: {tariff.name} для служби ID {tariff.service_id}"
            )
        else:
            tariff = existing

        service_name = [k for k, v in services.items() if v.id == tariff.service_id][0]
        if service_name not in tariffs:
            tariffs[service_name] = {}
        tariffs[service_name][tariff.name] = tariff

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
        {"name": "Водопостачання", "unit": "м³", "meter_number": None},
        {"name": "Газопостачання", "unit": "м³", "meter_number": None},
        {"name": "Електроенергія", "unit": "кВт·год", "meter_number": None},
        {"name": "Квартплата", "unit": "міс", "meter_number": None},
        {"name": "Вивіз сміття", "unit": "міс", "meter_number": None}
    ]
    
    for config in service_configs:
        service = db.session.query(UtilityService).filter_by(
            user_id=USER_ID, address_id=address_id, name=config["name"]
        ).first()
        if not service:
            service = UtilityService(
                user_id=USER_ID, address_id=address_id, name=config["name"],
                unit=config["unit"], meter_number=config["meter_number"], is_active=True
            )
            db.session.add(service)
            db.session.flush()
            logger.info(f"Створено службу: {config['name']}")
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
        tariffs = create_tariffs(services)
        
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
                import_water_reading(address.id, services["Водопостачання"].id, tariffs["Водопостачання"]["Базовий"].id, period, 
                                   water_reading, water_consumption, water_amount, reading_date, is_paid)
                imported_count += 1
            
            if gas_reading is not None:
                import_gas_reading(address.id, services["Газопостачання"].id, tariffs["Газопостачання"]["Стандартний"].id, period,
                                 gas_reading, gas_consumption, gas_amount, reading_date, is_paid)
                imported_count += 1
            
            # Імпорт електроенергії
            if reading_date < datetime(2025, 1, 1).date():
                # До 2025 - сума до оплати
                if electricity_amount is not None:
                    import_electricity_reading(address.id, services["Електроенергія"].id, tariffs["Електроенергія"]["Загальний"].id, period,
                                              0, None, electricity_amount, reading_date, is_paid, "Сума до оплати")
                    imported_count += 1
            else:
                # З 2025 - показники день і ніч
                if electricity_day is not None:
                    import_electricity_reading(address.id, services["Електроенергія"].id, tariffs["Електроенергія"]["Денний"].id, period,
                                              electricity_day, None, None, reading_date, is_paid, "Денний тариф")
                    imported_count += 1
                if electricity_night is not None:
                    import_electricity_reading(address.id, services["Електроенергія"].id, tariffs["Електроенергія"]["Нічний"].id, period,
                                              electricity_night, None, None, reading_date, is_paid, "Нічний тариф")
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

def import_water_reading(address_id, service_id, tariff_id, period, current_reading, consumption, amount, reading_date, is_paid):
    """Імпортує показник води"""
    existing = db.session.query(UtilityReading).filter_by(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period, tariff_id=tariff_id
    ).first()
    if existing:
        logger.info(f"Показник води за {period} вже існує")
        return
    
    reading = UtilityReading(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period,
        current_reading=current_reading, consumption=consumption, tariff_id=tariff_id,
        amount=amount, reading_date=datetime.combine(reading_date, datetime.min.time()).replace(tzinfo=timezone.utc),
        is_paid=is_paid
    )
    db.session.add(reading)
    logger.info(f"Додано показник води: {period} - показник:{current_reading}, спожито:{consumption}, сума:{amount}")

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
    existing = db.session.query(UtilityReading).filter_by(
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period
    ).first()
    if existing:
        logger.info(f"Показник електроенергії за {period} вже існує")
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
        user_id=USER_ID, address_id=address_id, service_id=service_id, period=period
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
