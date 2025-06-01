# _*_ coding:UTF-8 _*_
import logging
import hashlib
import datetime
import re
from typing import List, Dict, Any

import pdfplumber
from io import BytesIO

from models.models import User
from api.schemas import PaymentData
from api.funcs import find_category, get_last_rate

logger = logging.getLogger()


def parse_erste_pdf(file_content: bytes) -> List[Dict[str, Any]]:
    """
    Парсинг PDF виписки Erste Bank Австрії
    
    Args:
        file_content: Вміст PDF файлу в байтах
        
    Returns:
        List[Dict]: Список транзакцій
    """
    transactions = []
    current_year = datetime.datetime.now().year
    
    try:
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                    
                # Розбиваємо текст на рядки
                lines = text.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Пропускаємо порожні рядки та заголовки
                    if (not line or 'BLZ' in line or 'BIC' in line or 'EUR' in line or 
                        'Viktor Holoshivskyi' in line or 'GUTHABEN' in line or
                        'Account Statement' in line or 'Zuletzt gültiger' in line):
                        continue
                    
                    # Парсимо різні типи транзакцій
                    transaction = None
                    
                    # George-Überweisung (переказ) - шукаємо в поточному та наступних рядках
                    if 'George-Überweisung' in line:
                        transaction = parse_george_transfer_multiline(lines[i:i+3], current_year)
                    
                    # E-COMM (електронна комерція) - також може бути на кількох рядках
                    elif 'E-COMM' in line:
                        transaction = parse_ecomm_transaction_multiline(lines[i:i+3], current_year)
                    
                    if transaction:
                        transactions.append(transaction)
                        
    except Exception as e:
        logger.error(f"Помилка при парсингу PDF Erste Bank: {e}")
        raise ValueError(f"Не вдалося прочитати PDF файл: {e}")
    
    return transactions

def parse_george_transfer_multiline(lines: List[str], year: int) -> Dict[str, Any] | None:
    """
    Парсинг George-Überweisung з кількох рядків
    """
    try:
        # Об'єднуємо рядки для пошуку інформації
        combined_text = ' '.join(line.strip() for line in lines if line.strip())
        
        # Шукаємо дату та суму в форматі: ДДММ сума-
        date_amount_pattern = r'(\d{4})\s+([\d,]+)-'
        date_amount_match = re.search(date_amount_pattern, combined_text)
        
        if not date_amount_match:
            return None
            
        date_str = date_amount_match.group(1)  # ДДММ
        amount_str = date_amount_match.group(2).replace(',', '.')  # Сума
        
        # Шукаємо ім'я отримувача (зазвичай в окремому рядку)
        recipient = "Transfer"
        for line in lines:
            line = line.strip()
            # Пропускаємо рядки з датами, сумами та George-Überweisung
            if (line and not re.search(r'\d{4}', line) and 
                'George-Überweisung' not in line and 
                not re.search(r'[\d,]+-', line)):
                recipient = f"George Transfer to {line}"
                break
        
        # Конвертуємо дату (ДДММ -> повна дата)
        day = int(date_str[:2])
        month = int(date_str[2:])
        transaction_date = datetime.datetime(year, month, day)
        
        return {
            'date': transaction_date,
            'description': recipient,
            'transaction_type': 'Transfer',
            'amount': float(amount_str),
            'currency': 'EUR'
        }
        
    except Exception as e:
        logger.error(f"Помилка при парсингу George переказу: {e}")
        return None

def parse_ecomm_transaction_multiline(lines: List[str], year: int) -> Dict[str, Any] | None:
    """
    Парсинг E-COMM транзакції з кількох рядків
    """
    try:
        # Об'єднуємо рядки
        combined_text = ' '.join(line.strip() for line in lines if line.strip())
        
        # Шукаємо дату в форматі ДД.ММ. та суму
        date_pattern = r'(\d{2}\.\d{2}\.)'
        time_pattern = r'(\d{2}:\d{2})'
        amount_pattern = r'(\d{4})\s+([\d,]+)-'
        
        date_match = re.search(date_pattern, combined_text)
        amount_match = re.search(amount_pattern, combined_text)
        
        if not date_match or not amount_match:
            return None
            
        date_str = date_match.group(1).rstrip('.')  # ДД.ММ
        amount_str = amount_match.group(2).replace(',', '.')
        
        # Шукаємо торговця (зазвичай після сум)
        merchant = "E-Commerce"
        for line in lines:
            line = line.strip()
            # Шукаємо рядок з назвою торговця (містить букви та може містити цифри)
            if (line and re.search(r'[A-Za-z]', line) and 
                'E-COMM' not in line and 
                not re.search(r'^\d{2}\.\d{2}\.$', line) and
                not re.search(r'^\d{2}:\d{2}$', line)):
                merchant = line
                break
        
        # Конвертуємо дату
        day, month = map(int, date_str.split('.'))
        transaction_date = datetime.datetime(year, month, day)
        
        return {
            'date': transaction_date,
            'description': merchant,
            'transaction_type': 'Purchase', 
            'amount': float(amount_str),
            'currency': 'EUR'
        }
        
    except Exception as e:
        logger.error(f"Помилка при парсингу E-COMM транзакції: {e}")
        return None

def erste_to_pmt(user: User, transaction: Dict[str, Any]) -> PaymentData | None:
    """
    Конвертує транзакцію Erste Bank в PaymentData
    
    Args:
        user: Користувач
        transaction: Дані транзакції з PDF
        
    Returns:
        PaymentData або None
    """
    try:
        # Пропускаємо позитивні суми (надходження) - в Erste вони без мінуса
        if transaction['amount'] > 0 and 'income' in transaction.get('description', '').lower():
            return None
            
        description = transaction['description']
        
        # Очищуємо опис від зайвих символів та пробілів
        description = re.sub(r'\s+', ' ', description).strip()
        
        category_id, is_deleted = find_category(user, description)
        
        # Створюємо унікальний ID для банківського платежу
        unique_string = f"erste_{user.id}_{transaction['date'].strftime('%Y%m%d')}_{description}_{transaction['amount']}"
        bank_payment_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        # Конвертуємо EUR в UAH
        eur_amount = abs(transaction['amount'])
        uah_amount = eur_amount * get_last_rate("EUR", transaction['date'])
        
        return PaymentData(
            user_id=user.id,
            rdate=transaction['date'],
            category_id=category_id,
            mydesc=description.replace("'", ""),
            amount=round(uah_amount),
            currency="EUR",
            type_payment="card",
            source="erste",
            bank_payment_id=bank_payment_id,
            currency_amount=eur_amount,
            is_deleted=is_deleted,
        )
        
    except Exception as e:
        logger.error(f"Помилка при конвертації транзакції Erste Bank: {e}")
        return None