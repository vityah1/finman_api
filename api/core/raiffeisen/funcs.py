# _*_ coding:UTF-8 _*_
import logging
import csv
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from io import StringIO

from models.models import User
from api.schemas import PaymentData
from api.funcs import find_category, get_last_rate

logger = logging.getLogger()


def parse_raiffeisen_csv(file_content: str) -> List[Dict[str, Any]]:
    """
    Parse Raiffeisen Bank CSV statement

    Args:
        file_content: CSV file content as string

    Returns:
        List[Dict]: List of transactions
    """
    transactions = []

    try:
        # Read CSV content
        lines = file_content.strip().split('\n')
        logger.info(f"Processing Raiffeisen CSV with {len(lines)} lines")

        # Find the header line with transaction data
        data_start_line = None
        for i, line in enumerate(lines):
            if 'Дата і час здійснення операції' in line and 'Сума у валюті рахунку' in line:
                data_start_line = i
                logger.info(f"Found transaction header at line {i}")
                break

        if data_start_line is None:
            logger.error("Cannot find transaction data header in CSV")
            logger.debug(f"First 20 lines: {lines[:20]}")
            # Також шукаємо альтернативні варіанти заголовків
            for i, line in enumerate(lines[:20]):
                if 'Дата' in line and 'операції' in line:
                    logger.debug(f"Found partial header at line {i}: {line}")
                if 'Сума' in line:
                    logger.debug(f"Found amount field at line {i}: {line}")
            raise ValueError("Cannot find transaction data header in CSV. Expected columns: 'Дата і час здійснення операції', 'Сума у валюті рахунку'")

        # Parse CSV starting from data header
        csv_content = '\n'.join(lines[data_start_line:])
        logger.debug(f"CSV content for parsing: {csv_content[:500]}...")

        reader = csv.DictReader(StringIO(csv_content), delimiter=';')

        for row_num, row in enumerate(reader):
            try:
                transaction = parse_transaction_row(row)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to parse row {row_num}: {e}")
                continue

        logger.info(f"Successfully parsed {len(transactions)} transactions")

    except Exception as e:
        logger.error(f"Error parsing Raiffeisen CSV: {e}", exc_info=True)
        raise ValueError(f"Failed to parse CSV file: {e}")

    return transactions


def parse_transaction_row(row: Dict[str, str]) -> Dict[str, Any] | None:
    """
    Parse a single transaction row from CSV

    Args:
        row: CSV row as dictionary

    Returns:
        Dict with transaction data or None if invalid
    """
    try:
        # Extract date (format: "31.08.2025 08:51:00")
        date_str = row.get('Дата і час здійснення операції', '').strip()
        if not date_str:
            return None

        # Parse date - take only date part, ignore time
        date_part = date_str.split(' ')[0]
        transaction_date = datetime.strptime(date_part, '%d.%m.%Y')

        # Extract description
        description = row.get('Деталі операції', '').strip()
        if not description:
            return None

        # Extract amounts
        amount_uah_str = row.get('Сума у валюті рахунку', '').strip()
        amount_currency_str = row.get('Сума у валюті операції', '').strip()
        currency_str = row.get('Валюта', '').strip()

        if not amount_uah_str:
            return None

        # Convert amounts
        amount_uah = float(amount_uah_str.replace(',', '.'))

        # Determine original currency and amount
        currency = currency_str if currency_str else "UAH"
        amount_currency = float(amount_currency_str.replace(',', '.')) if amount_currency_str else amount_uah

        # Extract additional fields
        card_number = row.get('Номер картки', '').strip()
        mcc = row.get('MCC', '').strip()
        commission = row.get('Сума комісій', '').strip()
        cashback = row.get('Сума кешбеку', '').strip()

        # Convert commission and cashback
        commission_amount = float(commission.replace(',', '.')) if commission else 0.0
        cashback_amount = float(cashback.replace(',', '.')) if cashback else 0.0

        return {
            'date': transaction_date,
            'description': description,
            'amount_uah': amount_uah,
            'amount_currency': amount_currency,
            'currency': currency,
            'card_number': card_number,
            'mcc': mcc,
            'commission': commission_amount,
            'cashback': cashback_amount
        }

    except Exception as e:
        logger.error(f"Error parsing transaction row: {e}", exc_info=True)
        logger.debug(f"Failed row data: {row}")
        return None


def raiffeisen_to_pmt(user: User, transaction: Dict[str, Any]) -> PaymentData | None:
    """
    Convert Raiffeisen transaction to PaymentData

    Args:
        user: User object
        transaction: Transaction data from CSV

    Returns:
        PaymentData object or None if should be skipped
    """
    try:
        # In Raiffeisen CSV, all transactions are expenses (positive amounts)
        # Skip transactions with zero or invalid amounts
        if transaction['amount_uah'] <= 0:
            return None

        description = transaction['description']

        # Clean description
        description = description.replace('"', '').strip()

        # Find category
        category_id, is_deleted = find_category(user, description)

        # Create unique bank payment ID
        unique_string = (f"raiffeisen_{user.id}_{transaction['date'].strftime('%Y%m%d')}_"
                        f"{description}_{abs(transaction['amount_uah'])}")
        bank_payment_id = hashlib.md5(unique_string.encode()).hexdigest()

        # Determine currency and amount
        currency = transaction['currency']
        currency_amount = transaction['amount_currency']

        # Convert to UAH if needed
        if currency != "UAH":
            try:
                uah_amount = transaction['amount_uah']
            except:
                uah_amount = currency_amount * get_last_rate(currency, transaction['date'])
        else:
            uah_amount = currency_amount

        return PaymentData(
            user_id=user.id,
            rdate=transaction['date'],
            category_id=category_id,
            mydesc=description.replace("'", ""),
            amount=round(uah_amount),
            currency=currency,
            type_payment="card",
            source="raiffeisen",
            bank_payment_id=bank_payment_id,
            currency_amount=currency_amount,
            is_deleted=is_deleted,
        )

    except Exception as e:
        logger.error(f"Error converting Raiffeisen transaction: {e}")
        return None


def extract_account_info(file_content: str) -> Dict[str, str]:
    """
    Extract account information from CSV header

    Args:
        file_content: CSV file content as string

    Returns:
        Dict with account information
    """
    try:
        lines = file_content.strip().split('\n')
        account_info = {}

        for line in lines:
            line = line.strip().replace('"', '')

            if 'Клієнт:' in line:
                account_info['client_name'] = line.replace('Клієнт:', '').strip()
            elif 'Рахунок:' in line:
                account_info['account_number'] = line.replace('Рахунок:', '').strip()
            elif 'Валюта рахунку:' in line:
                account_info['account_currency'] = line.replace('Валюта рахунку:', '').strip()
            elif 'Період:' in line:
                account_info['period'] = line.replace('Період:', '').strip()
            elif 'Баланс на початок періоду:' in line:
                account_info['start_balance'] = line.replace('Баланс на початок періоду:', '').strip()
            elif 'Баланс на кінець періоду:' in line:
                account_info['end_balance'] = line.replace('Баланс на кінець періоду:', '').strip()

        return account_info

    except Exception as e:
        logger.error(f"Error extracting account info: {e}")
        return {}