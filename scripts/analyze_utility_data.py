#!/usr/bin/env python3
"""
Аналіз показників комунальних послуг - останні 3 періоди
"""

import sys
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Додаємо шлях до проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odf import opendocument
from odf.table import Table, TableRow, TableCell
from odf.text import P


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


def main():
    """Головна функція аналізу"""
    try:
        print("=== АНАЛІЗ ПОКАЗНИКІВ КОМУНАЛЬНИХ ПОСЛУГ ===")
        print("Файл: scripts/utility_ks6b27.ods")
        print()
        
        # Завантажуємо ODS файл
        doc = opendocument.load("scripts/utility_ks6b27.ods")
        tables = doc.getElementsByType(Table)
        table = tables[0]
        rows = table.getElementsByType(TableRow)
        
        # Збираємо всі дані
        data_rows = []
        
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
                period_date = date - relativedelta(months=1)
                period = period_date.strftime('%Y-%m')
            except:
                continue
            
            # Показники
            water_reading = parse_number(get_cell_value(cells[1]))
            gas_reading = parse_number(get_cell_value(cells[7]))
            electricity_day_reading = parse_number(get_cell_value(cells[11]))
            electricity_night_reading = parse_number(get_cell_value(cells[12]))
            
            # Квартплата та сміття
            rent_amount = 0
            garbage_amount = 0
            
            if len(cells) > 14:
                rent_amount = parse_number(get_cell_value(cells[14]))
            
            if len(cells) > 16:
                garbage_amount = parse_number(get_cell_value(cells[16]))
            
            data_rows.append({
                'date': date,
                'period': period,
                'date_str': date_str,
                'water_reading': water_reading,
                'gas_reading': gas_reading,
                'electricity_day_reading': electricity_day_reading,
                'electricity_night_reading': electricity_night_reading,
                'rent_amount': rent_amount,
                'garbage_amount': garbage_amount,
                'raw_data': {
                    'col_1': get_cell_value(cells[1]),
                    'col_7': get_cell_value(cells[7]),
                    'col_11': get_cell_value(cells[11]),
                    'col_12': get_cell_value(cells[12]),
                    'col_14': get_cell_value(cells[14]) if len(cells) > 14 else '',
                    'col_16': get_cell_value(cells[16]) if len(cells) > 16 else '',
                }
            })
        
        # Сортуємо по даті та беремо останні 3 періоди
        data_rows.sort(key=lambda x: x['date'])
        last_3_periods = data_rows[-3:]
        
        print("=== ОСТАННІ 3 ПЕРІОДИ ===")
        print()
        
        for i, row in enumerate(last_3_periods, 1):
            print(f"ПЕРІОД {i}: {row['period']} (дата в файлі: {row['date_str']})")
            print("=" * 50)
            
            print(f"ВОДА (колонка 1):")
            print(f"  Сире значення: '{row['raw_data']['col_1']}'")
            print(f"  Парсинг: {row['water_reading']}")
            print()
            
            print(f"ГАЗ (колонка 7):")
            print(f"  Сире значення: '{row['raw_data']['col_7']}'")
            print(f"  Парсинг: {row['gas_reading']}")
            print()
            
            print(f"ЕЛЕКТРИКА ДЕНЬ (колонка 11):")
            print(f"  Сире значення: '{row['raw_data']['col_11']}'")
            print(f"  Парсинг: {row['electricity_day_reading']}")
            print()
            
            print(f"ЕЛЕКТРИКА НІЧ (колонка 12):")
            print(f"  Сире значення: '{row['raw_data']['col_12']}'")
            print(f"  Парсинг: {row['electricity_night_reading']}")
            print()
            
            print(f"КВАРТПЛАТА (колонка 14):")
            print(f"  Сире значення: '{row['raw_data']['col_14']}'")
            print(f"  Парсинг: {row['rent_amount']}")
            print()
            
            print(f"СМІТТЯ (колонка 16):")
            print(f"  Сире значення: '{row['raw_data']['col_16']}'")
            print(f"  Парсинг: {row['garbage_amount']}")
            print()
            print("=" * 50)
            print()
        
        print("Аналіз завершено!")
        
    except Exception as e:
        print(f"Помилка під час аналізу: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
