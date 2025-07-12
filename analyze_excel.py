#!/usr/bin/env python3
import pandas as pd

# Читаємо Excel файл
try:
    df = pd.read_excel('scripts/utility_ks6b27.xlsx', header=None)
    print('АНАЛІЗ EXCEL ФАЙЛУ UTILITY_KS6B27.XLSX')
    print('=' * 80)
    print(f'Розмір таблиці: {df.shape[0]} рядків, {df.shape[1]} колонок')
    print()
    
    print('ПЕРШІ 10 РЯДКІВ (включно з заголовками):')
    print('-' * 80)
    for i in range(min(10, len(df))):
        row_data = []
        for j in range(min(25, len(df.columns))):
            value = df.iloc[i, j]
            if pd.notna(value) and str(value).strip() != '':
                row_data.append(f'Кол.{j}: "{value}"')
        if row_data:
            print(f'Рядок {i+1}: {", ".join(row_data)}')
        else:
            print(f'Рядок {i+1}: (порожній)')
    
    print()
    print('ОСТАННІ 5 РЯДКІВ:')
    print('-' * 80)
    for i in range(max(0, len(df)-5), len(df)):
        row_data = []
        for j in range(min(25, len(df.columns))):
            value = df.iloc[i, j]
            if pd.notna(value) and str(value).strip() != '':
                row_data.append(f'Кол.{j}: "{value}"')
        if row_data:
            print(f'Рядок {i+1}: {", ".join(row_data)}')
        else:
            print(f'Рядок {i+1}: (порожній)')

except FileNotFoundError:
    print('Файл utility_ks6b27.xlsx не знайдено, спробуємо .xls')
    try:
        df = pd.read_excel('scripts/utility_ks6b27.xls', header=None)
        print('АНАЛІЗ EXCEL ФАЙЛУ UTILITY_KS6B27.XLS')
        print('=' * 80)
        print(f'Розмір таблиці: {df.shape[0]} рядків, {df.shape[1]} колонок')
        print()
        
        print('ПЕРШІ 10 РЯДКІВ (включно з заголовками):')
        print('-' * 80)
        for i in range(min(10, len(df))):
            row_data = []
            for j in range(min(25, len(df.columns))):
                value = df.iloc[i, j]
                if pd.notna(value) and str(value).strip() != '':
                    row_data.append(f'Кол.{j}: "{value}"')
            if row_data:
                print(f'Рядок {i+1}: {", ".join(row_data)}')
            else:
                print(f'Рядок {i+1}: (порожній)')
        
        print()
        print('ОСТАННІ 5 РЯДКІВ:')
        print('-' * 80)
        for i in range(max(0, len(df)-5), len(df)):
            row_data = []
            for j in range(min(25, len(df.columns))):
                value = df.iloc[i, j]
                if pd.notna(value) and str(value).strip() != '':
                    row_data.append(f'Кол.{j}: "{value}"')
            if row_data:
                print(f'Рядок {i+1}: {", ".join(row_data)}')
            else:
                print(f'Рядок {i+1}: (порожній)')
                
    except Exception as e:
        print(f'Помилка читання файлу: {e}')

except Exception as e:
    print(f'Помилка: {e}')