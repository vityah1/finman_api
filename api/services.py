# _*_ coding:UTF-8 _*_
import logging
import io
from typing import Any, List, Dict, Optional

from fastapi import HTTPException, UploadFile, status
from pandas import read_csv, read_excel

from api.core.funcs import p24_to_pmt
from api.core.revolut.funcs import revolut_to_pmt
from api.core.wise.funcs import wise_to_pmt
from api.core.pumb.funcs import parse_pumb_pdf, pumb_to_pmt
from api.core.erste.funcs import parse_erste_pdf, erste_to_pmt
from api.funcs import add_bulk_payments
from api.mono.funcs import add_new_payment
from models import User
from mydb import db

logger = logging.getLogger()


async def bank_import(user: User, bank: str, file: UploadFile, action: str = "import"):
    """
    Імпорт даних з банківських виписок

    Параметри:
        user_id: ID користувача
        bank: Назва банку ("wise", "mono", "revolut", "p24", "pumb", "erste")
        file: Завантажений файл через FastAPI UploadFile
        action: Дія - "show" для попереднього перегляду або "import" для імпорту даних
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Файл не знайдено в запиті')

    if file.filename == '':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Не вказано імя файлу')

    try:
        # Зчитуємо вміст файлу
        file_content = await file.read()

        # Перетворюємо дані
        data_ = await convert_file_to_data(user, file_content, file.filename, bank)

        if not data_:
            logger.error("Невалідні дані у файлі")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невалідні дані у файлі")

        if action == 'show':
            return data_

        if action == 'import':
            result = add_bulk_payments(data_)
            if result:
                for pmt_row in data_:
                    pmt_row['sql'] = True
            else:
                for pmt_row in data_:
                    result = add_new_payment(pmt_row)
                    if result:
                        pmt_row['sql'] = True
                    else:
                        pmt_row['sql'] = False
        return data_
    except HTTPException:
        # Передаємо HTTPException без змін
        raise
    except Exception as err:
        from sqlalchemy.exc import IntegrityError
        # Дозволяємо IntegrityError пройти до глобального обробника
        if isinstance(err, IntegrityError):
            raise err
        logger.error(f'Помилка при імпорті даних: {err}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Помилка при імпорті файлу: {str(err)}")


async def convert_file_to_data(user: User, file_content: bytes, filename: str, bank: str) -> List[Dict[str, Any]]:
    """
    Перетворює завантажений файл на дані платежів

    Параметри:
        user: Об'єкт користувача
        file_content: Вміст файлу в бінарному форматі
        filename: Ім'я файлу
        bank: Назва банку
    """
    data = []

    # Обробка PDF файлів PUMB
    if bank == 'pumb':
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Для PUMB банку підтримуються тільки PDF файли'
            )
        
        # Парсимо PDF та конвертуємо транзакції
        transactions = parse_pumb_pdf(file_content)
        
        for transaction in transactions:
            pmt = pumb_to_pmt(user, transaction)
            if pmt:
                data.append(pmt.model_dump())
        
        return data

    # Обробка PDF файлів Erste Bank
    if bank == 'erste':
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Для Erste Bank підтримуються тільки PDF файли'
            )
        
        # Парсимо PDF та конвертуємо транзакції
        transactions = parse_erste_pdf(file_content)
        
        for transaction in transactions:
            pmt = erste_to_pmt(user, transaction)
            if pmt:
                data.append(pmt.model_dump())
        
        return data

    # Створюємо об'єкт для читання файлу
    file_obj = io.BytesIO(file_content)

    # Читаємо файл залежно від формату
    if '.xls' in filename.lower():
        df = read_excel(file_obj)
    elif '.csv' in filename.lower():
        df = read_csv(
            file_obj,
            delimiter=',',
            parse_dates=['Date'],
            date_format='%d-%m-%Y',
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Невідомий тип файлу: {filename}. Підтримуються .xls, .xlsx, .csv та .pdf (для PUMB та Erste Bank)'
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Файл {filename} порожній'
        )

    for _, row in df.iterrows():
        pmt = None
        # Обробляємо дані залежно від банку
        match bank:
            case 'revolut':
                pmt = revolut_to_pmt(user, row)
            case 'wise':
                pmt = wise_to_pmt(user, row)
            case 'p24':
                pmt = p24_to_pmt(user, row)
            case 'pumb':
                # PUMB обробляється окремо вище
                continue
            case 'erste':
                # Erste обробляється окремо вище
                continue
            case _:
                logger.warning(f"Непідтримуваний банк: {bank}")
                pmt = None

        if pmt:
            data.append(pmt.model_dump())

    return data
