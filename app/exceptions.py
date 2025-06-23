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
        logger.warning(f'=== 404 НЕ ЗНАЙДЕНО ===')
        logger.warning(f'URL: {request.url}')
        logger.warning(f'Method: {request.method}')
        logger.warning(f'Деталі: {exc.detail}')
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
        import traceback
        
        logger.error(f'=== ПОМИЛКА ЦІЛІСНОСТІ БД ===')
        logger.error(f'URL: {request.url}')
        logger.error(f'Method: {request.method}')
        logger.error(f'Помилка: {exc}')
        logger.error(f'ПОВНИЙ ТРЕЙС:\n{traceback.format_exc()}')
        logger.error(f'=== КІНЕЦЬ ТРЕЙСУ ===')

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
        import traceback
        
        logger.error(f'=== ПОМИЛКА ВАЛІДАЦІЇ PYDANTIC ===')
        logger.error(f'URL: {request.url}')
        logger.error(f'Method: {request.method}')
        logger.error(f'Помилка: {exc}')
        logger.error(f'ПОВНИЙ ТРЕЙС:\n{traceback.format_exc()}')
        logger.error(f'=== КІНЕЦЬ ТРЕЙСУ ===')
        
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
        import traceback
        
        # Якщо це вже відформатована помилка FastAPI, не переобробляємо її
        if isinstance(exc, HTTPException):
            logger.error(f'HTTP помилка {exc.status_code}: {exc.detail}')
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": str(exc.detail)}
            )

        # Логуємо необроблені помилки з повним трейсом
        logger.error(f'=== ЗАГАЛЬНА ПОМИЛКА ===')
        logger.error(f'URL: {request.url}')
        logger.error(f'Method: {request.method}')
        logger.error(f'Помилка: {str(exc)}')
        logger.error(f'Тип помилки: {exc.__class__.__name__}')
        logger.error(f'=== ПОВНИЙ ТРЕЙС ===')
        logger.error(traceback.format_exc())
        logger.error(f'=== КІНЕЦЬ ТРЕЙСУ ===')

        # В продакшн режимі не відображаємо деталі помилки клієнту
        from app.config import DEBUG
        if DEBUG:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": str(exc),
                    "error_type": exc.__class__.__name__,
                    "traceback": traceback.format_exc().split('\n')
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"detail": "Неочікувана помилка"}
            )
