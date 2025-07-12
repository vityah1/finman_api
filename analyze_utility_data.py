#!/usr/bin/env python3

import sys
sys.path.append('/home/vik/pets/finman_api')

from odf import opendocument
from odf.table import Table, TableRow, TableCell
from odf.text import P
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

# Завантажуємо ODS файл
doc = opendocument.load('scripts/utility_ks6b27.ods')
tables = doc.getElementsByType(Table)
table = tables[0]
rows = table.getElementsByType(TableRow)

print('=== АНАЛІЗ ПОКАЗНИКІВ КОМУНАЛЬНИХ ПОСЛУГ ===')
print('Структура файлу:')
print('Колонка 0: Дата')
print('Колонка 1: Показники води')
print('Колонка 7: Показники газу')  
print('Колонка 11: Показники електрики (день)')
print('Колонка 12: Показники електрики (ніч)')
print('Колонка 14: Квартплата')
print('Колонка 16: Сміття')
print()

# Збираємо всі періоди
periods_data = []

for i, row in enumerate(rows):
    if i < 2:  # Пропускаємо заголовки
        continue
        
    cells = row.getElementsByType(TableCell)
    if len(cells) < 14:
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
    
    # Показники
    water_reading = parse_number(get_cell_value(cells[1]))
    gas_reading = parse_number(get_cell_value(cells[7]))
    electricity_day_reading = parse_number(get_cell_value(cells[11]))
    electricity_night_reading = parse_number(get_cell_value(cells[12]))
    
    # Квартплата та сміття (суми)
    rent_amount = 0
    garbage_amount = 0
    
    if len(cells) > 14:
        rent_amount = parse_number(get_cell_value(cells[14]))
        
    if len(cells) > 16:
        garbage_amount = parse_number(get_cell_value(cells[16]))
    
    periods_data.append({
        'period': period,
        'date': date,
        'water': water_reading,
        'gas': gas_reading,
        'electricity_day': electricity_day_reading,
        'electricity_night': electricity_night_reading,
        'rent': rent_amount,
        'garbage': garbage_amount,
        'raw_date': date_str,
        'raw_water': get_cell_value(cells[1]),
        'raw_gas': get_cell_value(cells[7]),
        'raw_elec_day': get_cell_value(cells[11]),
        'raw_elec_night': get_cell_value(cells[12]),
        'raw_rent': get_cell_value(cells[14]) if len(cells) > 14 else '',
        'raw_garbage': get_cell_value(cells[16]) if len(cells) > 16 else ''
    })

# Сортуємо по даті і беремо останні 3 періоди
periods_data.sort(key=lambda x: x['date'], reverse=True)
last_3_periods = periods_data[:3]

print('=== ОСТАННІ 3 ПЕРІОДИ ===')
for i, data in enumerate(last_3_periods):
    print(f'\n{i+1}. ПЕРІОД {data["period"]} (дата файлу: {data["raw_date"]})')
    print(f'   Вода: {data["water"]} м³ (raw: "{data["raw_water"]}")')
    print(f'   Газ: {data["gas"]} м³ (raw: "{data["raw_gas"]}")')
    print(f'   Електрика день: {data["electricity_day"]} кВт·год (raw: "{data["raw_elec_day"]}")')
    print(f'   Електрика ніч: {data["electricity_night"]} кВт·год (raw: "{data["raw_elec_night"]}")')
    print(f'   Квартплата: {data["rent"]} грн (raw: "{data["raw_rent"]}")')
    print(f'   Сміття: {data["garbage"]} грн (raw: "{data["raw_garbage"]}")')

print('\n=== ЗАГАЛЬНА КІЛЬКІСТЬ ПЕРІОДІВ У ФАЙЛІ ===')
print(f'Всього знайдено періодів: {len(periods_data)}')
