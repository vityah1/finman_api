from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
import re
import logging

logger = logging.getLogger(__name__)

def register_exception_handlers(app):
    """
    Реєструє обробники винятків для FastAPI додатку
    """
    @app.exception_handler(404)
    async def page_not_found(request: Request, exc: HTTPException):
        logger.error(f'Resource not found: {request.url.path}')
        return JSONResponse(
            status_code=404,
            content={"message": f"{exc.detail}, path: {request.url.path}"}
        )
    
    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        """
        Обробляє помилки цілісності бази даних (IntegrityError)
        Відправляє зрозуміле повідомлення про помилку та відповідний HTTP статус
        """
        logger.error(f'Помилка цілісності бази даних: {exc}')
        
        error_message = str(exc)
        response = {"message": "Помилка в базі даних"}
        status_code = 500
        
        # Обробка помилок дублікатів
        if '1062' in error_message and 'Duplicate entry' in error_message:
            duplicated_info = re.search(r"Duplicate entry '(.*?)' for key '(.*?)'", error_message)
            if duplicated_info:
                duplicated_value = duplicated_info.group(1)
                key_name = duplicated_info.group(2)
                response = {
                    "message": f"Запис з таким значенням вже існує",
                    "details": {
                        "duplicated_value": duplicated_value,
                        "key": key_name
                    }
                }
                status_code = 409  # Conflict
        
        # Обробка помилок foreign key
        elif '1452' in error_message and 'foreign key constraint fails' in error_message.lower():
            fk_info = re.search(r"FOREIGN KEY \(`(.*?)`\) REFERENCES `(.*?)`", error_message)
            if fk_info:
                field_name = fk_info.group(1)
                reference_table = fk_info.group(2)
                response = {
                    "message": f"Некоректне значення зовнішнього ключа",
                    "details": {
                        "field": field_name,
                        "reference_table": reference_table
                    }
                }
                status_code = 400  # Bad Request
        
        return JSONResponse(status_code=status_code, content=response)
    
    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        """
        Загальний обробник помилок, який краще обробляє неочікувані помилки
        Цей обробник буде використаний тільки якщо помилка не була оброблена іншими обробниками
        """
        # Якщо це вже відформатована помилка FastAPI, не переобробляємо її
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={"message": str(exc.detail)}
            )
        
        # Логуємо необроблені помилки
        logger.error(f'Загальна помилка: {str(exc)}')
        
        # В продакшн режимі не відображаємо деталі помилки клієнту
        from app.config import DEBUG
        if DEBUG:
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Неочікувана помилка",
                    "error": str(exc),
                    "type": exc.__class__.__name__
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"message": "Неочікувана помилка. Перевірте логи сервера."}
            )
