#!/usr/bin/env python3
from odf import opendocument
from odf.table import Table, TableRow, TableCell
from odf.text import P

def get_cell_value(cell):
    ps = cell.getElementsByType(P)
    text_content = ''
    for p in ps:
        text_content += str(p)
    return text_content

doc = opendocument.load('scripts/utility_ks6b27.ods')
tables = doc.getElementsByType(Table)
table = tables[0]
rows = table.getElementsByType(TableRow)

print('ПОВНИЙ АНАЛІЗ ФАЙЛУ UTILITY_KS6B27.ODS')
print('=' * 80)

# Читаємо перші 5 рядків (заголовки)
print('ЗАГОЛОВКИ (перші 5 рядків):')
for i in range(min(5, len(rows))):
    row = rows[i]
    cells = row.getElementsByType(TableCell)
    print(f'Рядок {i+1}:')
    for j, cell in enumerate(cells[:25]):  # Перші 25 колонок
        value = get_cell_value(cell).strip()
        if value:
            print(f'  Кол.{j}: "{value}"')
    print()

print('КІЛЬКА ПРИКЛАДІВ ДАНИХ (рядки 6-10):')

for i in range(5, min(10, len(rows))):
    row = rows[i]
    cells = row.getElementsByType(TableCell)
    
    date_val = get_cell_value(cells[0]).strip() if len(cells) > 0 else ''
    if not date_val:
        continue
        
    print(f'Рядок {i+1} (дата: {date_val}):')
    for j in range(min(25, len(cells))):
        value = get_cell_value(cells[j]).strip()
        if value and value != '0':
            print(f'  Кол.{j}: "{value}"')
    print()