from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
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
            content={"detail": f"{exc.detail}, path: {request.url.path}"}
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        """
        Обробляє помилки цілісності бази даних (IntegrityError)
        Відправляє зрозуміле повідомлення про помилку без розкриття структури БД
        """
        logger.error(f'Помилка цілісності бази даних: {exc}')

        error_message = str(exc)

        # Обробка помилок дублікатів
        if '1062' in error_message and 'Duplicate entry' in error_message:
            return JSONResponse(
                status_code=409,
                content={"detail": "Помилка цілосності БД: запис з такими даними вже існує"}
            )

        # Обробка помилок foreign key
        elif '1452' in error_message and 'foreign key constraint fails' in error_message.lower():
            return JSONResponse(
                status_code=400,
                content={"detail": "Помилка цілосності БД: некоректне посилання на пов'язані дані"}
            )

        # Обробка інших помилок цілісності
        elif '1048' in error_message and 'cannot be null' in error_message.lower():
            return JSONResponse(
                status_code=400,
                content={"detail": "Помилка цілосності БД: відсутні обов'язкові дані"}
            )

        # Загальна помилка цілісності
        return JSONResponse(
            status_code=500,
            content={"detail": "Помилка цілосності БД"}
        )
        
    # Додаємо обробник для помилок валідації Pydantic
    from pydantic import ValidationError
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.error(f'Помилка валідації Pydantic: {exc}')
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Помилка валідації даних",
                "errors": exc.errors() if hasattr(exc, 'errors') else str(exc)
            }
        )

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
                content={"detail": str(exc.detail)}
            )

        # Логуємо необроблені помилки
        logger.error(f'Загальна помилка: {str(exc)}', exc_info=True)  # Додаємо exc_info=True для виведення стеку викликів

        # В продакшн режимі не відображаємо деталі помилки клієнту
        from app.config import DEBUG
        if DEBUG:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": str(exc),
                    "error_type": exc.__class__.__name__
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": "Неочікувана помилка"}
            )
