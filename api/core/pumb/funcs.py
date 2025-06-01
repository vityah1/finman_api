# _*_ coding:UTF-8 _*_
import logging
import hashlib
import datetime
import re
import time
from decimal import Decimal
from typing import List, Dict, Any

import pdfplumber
from io import BytesIO

from models.models import User
from api.schemas import PaymentData
from api.funcs import find_category

logger = logging.getLogger()


def parse_pumb_pdf(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Парсинг PDF виписки ПУМБ банку
    
    Args:
        file_content: Вміст PDF файлу в байтах
        
    Returns:
        List[Dict]: Список транзакцій
    """
    transactions = []
    transaction_counter = 0  # Лічильник для унікальності
    
    try:
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                    
                # Розбиваємо текст на рядки
                lines = text.split('\n')
                
                # Знаходимо блок з операціями
                in_operations_section = False
                
                for line in lines:
                    line = line.strip()
                    
                    # Початок секції операцій
                    if 'Операції за кредитною карткою' in line:
                        in_operations_section = True
                        continue
                    
                    # Кінець секції операцій    
                    if in_operations_section and ('По рахунку' in line or 'Всього списано:' in line):
                        in_operations_section = False
                        continue
                    
                    # Пропускаємо заголовки та порожні рядки
                    if (not in_operations_section or not line or 
                        'Дата операції' in line or 'Картка' in line or 
                        'Опис операції' in line or 'Тип транзакції' in line or
                        'Сума в валюті' in line or 'Сума в гривнях' in line):
                        continue
                    
                    # Парсимо рядок транзакції
                    transaction = parse_transaction_line(line)
                    if transaction:
                        transaction_counter += 1
                        transaction['sequence_number'] = transaction_counter  # Додаємо порядковий номер
                        transactions.append(transaction)
                        
    except Exception as e:
        logger.error(f"Помилка при парсингу PDF ПУМБ: {e}")
        raise ValueError(f"Не вдалося прочитати PDF файл: {e}")
    
    return transactions

def parse_transaction_line(line: str) -> Dict[str, Any] | None:
    """
    Парсинг рядка транзакції з PDF
    
    Формат: ДД.ММ.РРРР Опис_операції Тип_транзакції Сума_в_валюті Сума_в_гривнях
    """
    try:
        # Регулярний вираз для парсингу рядка транзакції
        # Шукаємо дату на початку рядка
        date_pattern = r'^(\d{2}\.\d{2}\.\d{4})\s+'
        date_match = re.match(date_pattern, line)
        
        if not date_match:
            return None
            
        date_str = date_match.group(1)
        remaining_line = line[date_match.end():].strip()
        
        # Шукаємо числові значення в кінці рядка (може бути формат 1 000.00 або 1000.00)
        amount_pattern = r'(\d{1,3}(?:\s\d{3})*(?:[,\.]\d{2})?)\s+(\d{1,3}(?:\s\d{3})*(?:[,\.]\d{2})?)$'
        amount_match = re.search(amount_pattern, remaining_line)
        
        if not amount_match:
            # Пробуємо простіший паттерн для чисел без пробілів
            amount_pattern = r'(\d+(?:[,\.]\d+)?)\s+(\d+(?:[,\.]\d+)?)$'
            amount_match = re.search(amount_pattern, remaining_line)
            
        if not amount_match:
            return None
            
        # Витягуємо суми та очищуємо від пробілів
        currency_amount_str = amount_match.group(1).replace(' ', '').replace(',', '.')
        uah_amount_str = amount_match.group(2).replace(' ', '').replace(',', '.')
        
        # Знаходимо опис операції (все між датою та сумами)
        description_end = amount_match.start()
        description_part = remaining_line[:description_end].strip()
        
        # Відокремлюємо тип операції (зазвичай останнє слово перед сумами)
        # Список можливих типів операцій в ПУМБ
        transaction_types = ['Покупка', 'Надходження', 'Переказ', 'Зняття', 'Поповнення']
        transaction_type = 'Покупка'  # За замовчуванням
        description = description_part
        
        for t_type in transaction_types:
            if description_part.endswith(t_type):
                transaction_type = t_type
                description = description_part[:-len(t_type)].strip()
                break
        
        # Конвертуємо дату
        transaction_date = datetime.datetime.strptime(date_str, '%d.%m.%Y')
        
        return {
            'date': transaction_date,
            'description': description,
            'transaction_type': transaction_type,
            'currency_amount': float(currency_amount_str),
            'uah_amount': float(uah_amount_str)
        }
        
    except Exception as e:
        logger.error(f"Помилка при парсингу рядка транзакції '{line}': {e}")
        return None

def pumb_to_pmt(user: User, transaction: Dict[str, Any]) -> PaymentData | None:
    """
    Конвертує транзакцію ПУМБ в PaymentData
    
    Args:
        user: Користувач
        transaction: Дані транзакції з PDF
        
    Returns:
        PaymentData або None
    """
    try:
        # Пропускаємо надходження (позитивні суми)
        if transaction['transaction_type'] == 'Надходження':
            return None
            
        description = transaction['description']
        
        # Очищуємо опис від зайвих символів
        description = re.sub(r'\s+', ' ', description).strip()
        
        category_id, is_deleted = find_category(user, description)
        
        # Створюємо унікальний ID для банківського платежу
        # Включаємо порядковий номер для гарантії унікальності
        unique_string = (f"pumb_{user.id}_{transaction['date'].strftime('%Y%m%d')}_"
                        f"{description}_{transaction['uah_amount']}_{transaction.get('sequence_number', 0)}_"
                        )  # Мікросекунди для унікальності
        bank_payment_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        # Визначаємо валюту та суму
        currency = "UAH"
        currency_amount = transaction['uah_amount']
        
        # Перевіряємо чи це валютна операція
        if abs(transaction['currency_amount'] - transaction['uah_amount']) > 0.01:
            # Розраховуємо курс для визначення валюти
            rate = transaction['uah_amount'] / transaction['currency_amount'] if transaction['currency_amount'] != 0 else 1
            
            # Визначаємо валюту за курсом (приблизні діапазони)
            if 35 <= rate <= 45:  # USD курс
                currency = "USD"
                currency_amount = transaction['currency_amount']
            elif 38 <= rate <= 48:  # EUR курс
                currency = "EUR"  
                currency_amount = transaction['currency_amount']
        
        return PaymentData(
            user_id=user.id,
            rdate=transaction['date'],
            category_id=category_id,
            mydesc=description.replace("'", ""),
            amount=round(abs(transaction['uah_amount'])),  # Використовуємо модуль для впевненості
            currency=currency,
            type_payment="card",
            source="pumb",
            bank_payment_id=bank_payment_id,
            currency_amount=abs(currency_amount),
            is_deleted=is_deleted,
        )
        
    except Exception as e:
        logger.error(f"Помилка при конвертації транзакції ПУМБ: {e}")
        return None