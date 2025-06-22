#!/usr/bin/env python3
"""
Скрипт імпорту комунальних показників з ODS файлу для адреси Карпатської Січі 6Б/27
Версія 2.0 - з правильною структурою служб та тарифів
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import logging
import traceback

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
from models.models import UtilityAddress, UtilityService, UtilityTariff, UtilityReading
from mydb import db
from sqlalchemy import or_

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

USER_ID = 1
ADDRESS_NAME = "Карпатська Січі 6Б/27"
ADDRESS_FULL = "м. Івано-Франківськ, вул. Карпатської Січі 6Б, кв. 27"


def clean_existing_data():
    """Очистити існуючі дані перед імпортом"""
    logger.info("Очищення існуючих даних...")
    
    # Видаляємо показники
    db.session.query(UtilityReading).filter(UtilityReading.user_id == USER_ID).delete()
    
    # Видаляємо тарифи
    db.session.query(UtilityTariff).filter(
        UtilityTariff.service_id.in_(
            db.session.query(UtilityService.id).filter(UtilityService.user_id == USER_ID)
        )
    ).delete(synchronize_session=False)
    
    # Видаляємо служби
    db.session.query(UtilityService).filter(UtilityService.user_id == USER_ID).delete()
    
    # Видаляємо адреси
    db.session.query(UtilityAddress).filter(UtilityAddress.user_id == USER_ID).delete()
    
    db.session.commit()
    logger.info("Очищення завершено")


def create_address():
    """Створити адресу"""
    address = UtilityAddress(
        user_id=USER_ID,
        name=ADDRESS_NAME,
        address=ADDRESS_FULL,
        description="Основна квартира",
        is_active=True
    )
    db.session.add(address)
    db.session.commit()
    logger.info(f"Створено адресу: {address.name} (ID: {address.id})")
    return address


def create_services(address_id):
    """Створити служби з правильною структурою"""
    services = {}
    
    # Вода - одна служба зі спільним показником
    water_service = UtilityService(
        user_id=USER_ID,
        address_id=address_id,
        name="Вода",
        description="Водопостачання та водовідведення",
        unit="м³",
        meter_number="водомір",
        is_active=True,
        has_shared_meter=True,  # Спільний показник для всіх тарифів
        service_group="water"
    )
    db.session.add(water_service)
    db.session.commit()
    services['water'] = water_service
    logger.info(f"Створено службу: {water_service.name} (ID: {water_service.id})")
    
    # Газ - одна служба зі спільним показником
    gas_service = UtilityService(
        user_id=USER_ID,
        address_id=address_id,
        name="Газопостачання",
        description="Природний газ",
        unit="м³",
        meter_number="газовий лічильник",
        is_active=True,
        has_shared_meter=True,  # Спільний показник для споживання + абонплата
        service_group="gas"
    )
    db.session.add(gas_service)
    db.session.commit()
    services['gas'] = gas_service
    logger.info(f"Створено службу: {gas_service.name} (ID: {gas_service.id})")
    
    # Електрика - окремі служби для день/ніч
    electricity_day = UtilityService(
        user_id=USER_ID,
        address_id=address_id,
        name="Електрика (день)",
        description="Денний тариф електроенергії",
        unit="кВт·год",
        meter_number="електролічильник",
        is_active=True,
        has_shared_meter=False,  # Окремий показник
        service_group="electricity"
    )
    db.session.add(electricity_day)
    db.session.commit()
    services['electricity_day'] = electricity_day
    logger.info(f"Створено службу: {electricity_day.name} (ID: {electricity_day.id})")
    
    electricity_night = UtilityService(
        user_id=USER_ID,
        address_id=address_id,
        name="Електрика (ніч)",
        description="Нічний тариф електроенергії",
        unit="кВт·год",
        meter_number="електролічильник",
        is_active=True,
        has_shared_meter=False,  # Окремий показник
        service_group="electricity"
    )
    db.session.add(electricity_night)
    db.session.commit()
    services['electricity_night'] = electricity_night
    logger.info(f"Створено службу: {electricity_night.name} (ID: {electricity_night.id})")
    
    # Квартплата
    rent_service = UtilityService(
        user_id=USER_ID,
        address_id=address_id,
        name="Квартплата",
        description="Щомісячна квартплата",
        unit="міс",
        is_active=True,
        has_shared_meter=False
    )
    db.session.add(rent_service)
    db.session.commit()
    services['rent'] = rent_service
    logger.info(f"Створено службу: {rent_service.name} (ID: {rent_service.id})")
    
    # Вивіз сміття
    garbage_service = UtilityService(
        user_id=USER_ID,
        address_id=address_id,
        name="Вивіз сміття",
        description="Вивіз побутових відходів",
        unit="міс",
        is_active=True,
        has_shared_meter=False
    )
    db.session.add(garbage_service)
    db.session.commit()
    services['garbage'] = garbage_service
    logger.info(f"Створено службу: {garbage_service.name} (ID: {garbage_service.id})")
    
    return services


def create_tariffs(services):
    """Створити тарифи з правильною структурою"""
    tariffs = {}
    
    # Тарифи для води - з різними періодами дії
    water_tariffs_data = [
        # 2021-08 до 2021-12
        {'name': 'Водопостачання', 'rate': 11.59, 'type': 'consumption', 'from': '2021-08-01', 'to': '2021-12-31'},
        {'name': 'Водовідведення', 'rate': 13.66, 'type': 'drainage', 'from': '2021-08-01', 'to': '2021-12-31'},
        {'name': 'Абонплата (вода)', 'rate': 0, 'type': 'subscription', 'from': '2021-08-01', 'to': '2021-12-31'},
        
        # 2022-01 до 2022-03
        {'name': 'Водопостачання', 'rate': 12.95, 'type': 'consumption', 'from': '2022-01-01', 'to': '2022-03-31'},
        {'name': 'Водовідведення', 'rate': 15.29, 'type': 'drainage', 'from': '2022-01-01', 'to': '2022-03-31'},
        {'name': 'Абонплата (вода)', 'rate': 14.17, 'type': 'subscription', 'from': '2022-01-01', 'to': '2022-03-31'},
        
        # 2022-04 і далі
        {'name': 'Водопостачання', 'rate': 12.95, 'type': 'consumption', 'from': '2022-04-01', 'to': None},
        {'name': 'Водовідведення', 'rate': 15.29, 'type': 'drainage', 'from': '2022-04-01', 'to': None},
        {'name': 'Абонплата (вода)', 'rate': 24.67, 'type': 'subscription', 'from': '2022-04-01', 'to': None},
    ]
    
    for data in water_tariffs_data:
        tariff = UtilityTariff(
            service_id=services['water'].id,
            name=f"{data['name']}-{data['from'][:7]}",
            rate=data['rate'],
            subscription_fee=0,  # Абонплата тепер в rate
            currency='UAH',
            valid_from=datetime.strptime(data['from'], '%Y-%m-%d'),
            valid_to=datetime.strptime(data['to'], '%Y-%m-%d') if data['to'] else None,
            is_active=data['to'] is None,  # Активний якщо немає дати закінчення
            tariff_type=data['type'],
            group_code='water'
        )
        db.session.add(tariff)
        tariffs[f"water_{data['type']}_{data['from'][:7]}"] = tariff
    
    # Тарифи для газу - ТІЛЬКИ ОДИН ПОСТІЙНИЙ ТАРИФ 7.99
    gas_tariff = UtilityTariff(
        service_id=services['gas'].id,
        name="Газ",
        rate=7.99,  # Постійний тариф з самого початку
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2021-08-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='consumption',
        group_code='gas'
    )
    db.session.add(gas_tariff)
    
    # Абонплата за газ
    gas_subscription = UtilityTariff(
        service_id=services['gas'].id,
        name="Абонплата (газ)",
        rate=264.0,  # Фіксована абонплата
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2021-08-01', '%Y-%m-%d'),
        is_active=True,
        tariff_type='subscription',
        group_code='gas'
    )
    db.session.add(gas_subscription)
    
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
    
    # Тариф для квартплати
    rent_tariff = UtilityTariff(
        service_id=services['rent'].id,
        name="Фіксований",
        rate=389.91,
        subscription_fee=0,
        currency='UAH',
        valid_from=datetime.strptime('2021-01-01', '%Y-%m-%d'),
        is_active=True
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
        is_active=True
    )
    db.session.add(garbage_tariff)
    
    db.session.commit()
    logger.info("Створено всі тарифи")
    return tariffs


def parse_number(value):
    """Парсинг числа з рядка"""
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Видаляємо пробіли та коми
    value = str(value).replace(' ', '').replace(',', '.')
    try:
        return float(value)
    except:
        return 0.0


def import_readings_from_ods(filename, services):
    """Імпорт показників з ODS файлу"""
    logger.info(f"Початок імпорту з файлу: {filename}")
    
    doc = load(filename)
    tables = doc.getElementsByType(Table)
    
    if not tables:
        logger.error("Не знайдено таблиць в документі")
        return
    
    table = tables[0]
    rows = table.getElementsByType(TableRow)
    
    # Пропускаємо заголовок
    data_rows = rows[1:]
    
    for row_idx, row in enumerate(data_rows):
        cells = row.getElementsByType(TableCell)
        if len(cells) < 15:  # Мінімальна кількість колонок
            continue
        
        try:
            # Читаємо дані з рядка
            date_str = get_cell_value(cells[0])
            if not date_str:
                continue
                
            # Парсимо дату
            try:
                date = datetime.strptime(date_str, '%d.%m.%Y')
                # ВАЖЛИВО: показники станом на 01.05.2025 - це дані за КВІТЕНЬ!
                # Тому віднімаємо 1 місяць
                period_date = date - relativedelta(months=1)
                period = period_date.strftime('%Y-%m')
            except:
                continue
            
            # Показники (беремо ПОКАЗНИКИ, а не споживання!)
            water_reading = parse_number(get_cell_value(cells[1]))     # Колонка 2 - показник води
            gas_reading = parse_number(get_cell_value(cells[7]))       # Колонка 8 - показник газу!!!
            electricity_day_reading = parse_number(get_cell_value(cells[12]))   # Колонка 13 - день
            electricity_night_reading = parse_number(get_cell_value(cells[11])) # Колонка 12 - ніч
            
            # Квартплата та сміття можуть бути відсутні в деяких рядках
            rent_amount = 0
            garbage_amount = 0
            
            if len(cells) > 14:
                rent_amount = parse_number(get_cell_value(cells[14]))      # Колонка O (15) - квартплата
            
            if len(cells) > 16:
                garbage_amount = parse_number(get_cell_value(cells[16]))   # Колонка Q (17) - сміття
            
            # Створюємо показники для води
            if water_reading > 0:
                # Для води створюємо показники для всіх активних тарифів
                water_tariffs = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id == services['water'].id,
                    UtilityTariff.valid_from <= date,
                    or_(UtilityTariff.valid_to.is_(None), UtilityTariff.valid_to >= date)
                ).all()
                
                for tariff in water_tariffs:
                    reading = UtilityReading(
                        user_id=USER_ID,
                        address_id=services['water'].address_id,
                        service_id=services['water'].id,
                        tariff_id=tariff.id,
                        period=period,
                        current_reading=water_reading,
                        reading_date=date,
                        is_paid=True  # Історичні дані вважаємо оплаченими
                    )
                    db.session.add(reading)
            
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
                        current_reading=gas_reading,
                        reading_date=date,
                        is_paid=True
                    )
                    db.session.add(reading)
            
            # Створюємо показники для електрики (день)
            if electricity_day_reading > 0:
                day_tariff = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id == services['electricity_day'].id,
                    UtilityTariff.is_active == True
                ).first()
                
                if day_tariff:
                    reading = UtilityReading(
                        user_id=USER_ID,
                        address_id=services['electricity_day'].address_id,
                        service_id=services['electricity_day'].id,
                        tariff_id=day_tariff.id,
                        period=period,
                        current_reading=electricity_day_reading,
                        reading_date=date,
                        is_paid=True
                    )
                    db.session.add(reading)
            
            # Створюємо показники для електрики (ніч)
            if electricity_night_reading > 0:
                night_tariff = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id == services['electricity_night'].id,
                    UtilityTariff.is_active == True
                ).first()
                
                if night_tariff:
                    reading = UtilityReading(
                        user_id=USER_ID,
                        address_id=services['electricity_night'].address_id,
                        service_id=services['electricity_night'].id,
                        tariff_id=night_tariff.id,
                        period=period,
                        current_reading=electricity_night_reading,
                        reading_date=date,
                        is_paid=True
                    )
                    db.session.add(reading)
            
            # Створюємо показники для квартплати
            if rent_amount > 0:
                rent_tariff = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id == services['rent'].id,
                    UtilityTariff.is_active == True
                ).first()
                
                if rent_tariff:
                    reading = UtilityReading(
                        user_id=USER_ID,
                        address_id=services['rent'].address_id,
                        service_id=services['rent'].id,
                        tariff_id=rent_tariff.id,
                        period=period,
                        current_reading=rent_amount,  # Для квартплати це сума, а не показник
                        reading_date=date,
                        is_paid=True
                    )
                    db.session.add(reading)
            
            # Створюємо показники для сміття
            if garbage_amount > 0:
                garbage_tariff = db.session.query(UtilityTariff).filter(
                    UtilityTariff.service_id == services['garbage'].id,
                    UtilityTariff.is_active == True
                ).first()
                
                if garbage_tariff:
                    reading = UtilityReading(
                        user_id=USER_ID,
                        address_id=services['garbage'].address_id,
                        service_id=services['garbage'].id,
                        tariff_id=garbage_tariff.id,
                        period=period,
                        current_reading=garbage_amount,  # Для сміття це сума, а не показник
                        reading_date=date,
                        is_paid=True
                    )
                    db.session.add(reading)
            
            # Зберігаємо кожні 10 рядків
            if (row_idx + 1) % 10 == 0:
                db.session.commit()
                logger.info(f"Оброблено {row_idx + 1} рядків")
                
        except Exception as e:
            logger.error(f"Помилка обробки рядка {row_idx + 1}: {e}")
            logger.error(traceback.format_exc())
            continue
    
    # Зберігаємо залишки
    db.session.commit()
    logger.info("Імпорт показників завершено")


def get_cell_value(cell):
    """Отримати значення з комірки"""
    paragraphs = cell.getElementsByType(P)
    if paragraphs:
        return str(paragraphs[0])
    return ""


def calculate_all_readings():
    """Розрахувати попередні показники та споживання для всіх записів"""
    logger.info("Розрахунок попередніх показників та споживання...")
    
    # Отримуємо всі показники
    readings = db.session.query(UtilityReading).filter(
        UtilityReading.user_id == USER_ID
    ).order_by(
        UtilityReading.service_id,
        UtilityReading.tariff_id,
        UtilityReading.period
    ).all()
    
    # Групуємо за службою та тарифом
    service_tariff_readings = {}
    for reading in readings:
        key = (reading.service_id, reading.tariff_id)
        if key not in service_tariff_readings:
            service_tariff_readings[key] = []
        service_tariff_readings[key].append(reading)
    
    # Розраховуємо для кожної групи
    for key, group_readings in service_tariff_readings.items():
        prev_reading = None
        
        # Перевіряємо чи це квартплата або сміття
        service_id = key[0]
        service = db.session.query(UtilityService).filter(UtilityService.id == service_id).first()
        
        for reading in group_readings:
            # Для квартплати та сміття - особлива логіка
            if service and service.name in ['Квартплата', 'Вивіз сміття']:
                # Це фіксовані суми, а не показники лічильників
                reading.previous_reading = 0
                reading.consumption = 0
                reading.amount = reading.current_reading  # current_reading тут містить суму
            elif prev_reading:
                reading.previous_reading = prev_reading.current_reading
                reading.consumption = reading.current_reading - prev_reading.current_reading
                
                # Розраховуємо суму
                if reading.tariff:
                    if reading.tariff.tariff_type == 'subscription':
                        # Для абонплати - фіксована сума
                        reading.amount = reading.tariff.rate
                    else:
                        # Для споживання - множимо на тариф
                        reading.amount = reading.consumption * reading.tariff.rate
            else:
                # Перший показник
                reading.previous_reading = 0
                reading.consumption = reading.current_reading
                if reading.tariff:
                    if reading.tariff.tariff_type == 'subscription':
                        reading.amount = reading.tariff.rate
                    else:
                        reading.amount = reading.consumption * reading.tariff.rate
            
            if not service or service.name not in ['Квартплата', 'Вивіз сміття']:
                prev_reading = reading
    
    db.session.commit()
    logger.info("Розрахунок завершено")


def main():
    """Основна функція"""
    logger.info("=== Початок імпорту комунальних даних ===")
    
    try:
        # Очищаємо існуючі дані
        clean_existing_data()
        
        # Створюємо адресу
        address = create_address()
        
        # Створюємо служби
        services = create_services(address.id)
        
        # Створюємо тарифи
        tariffs = create_tariffs(services)
        
        # Імпортуємо показники з файлу
        ods_file = os.path.join(os.path.dirname(__file__), 'utility_ks6b27.ods')
        if os.path.exists(ods_file):
            import_readings_from_ods(ods_file, services)
            
            # Розраховуємо попередні показники та споживання
            calculate_all_readings()
        else:
            logger.warning(f"Файл {ods_file} не знайдено. Імпорт показників пропущено.")
        
        logger.info("=== Імпорт успішно завершено ===")
        
    except Exception as e:
        logger.error(f"Помилка імпорту: {e}")
        logger.error(traceback.format_exc())
        db.session.rollback()
        raise


if __name__ == "__main__":
    main()
