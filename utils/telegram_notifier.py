import os
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Сервіс для відправки повідомлень про помилки в Telegram адміністратору
    """
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '461986981:AAGHyTw5Na_o_9ln1GXjPV5zhwU6mR52Svc')
        self.admin_chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '190722186')
        self.enabled = bool(self.bot_token)
        
        if not self.enabled:
            logger.warning("TELEGRAM_BOT_TOKEN не знайдено в environment variables. Telegram повідомлення вимкнені.")
        else:
            logger.info(f"Telegram повідомлення увімкнені. Чат адміністратора: {self.admin_chat_id}")
    
    def get_user_info(self, user_id: int) -> dict:
        """
        Отримати інформацію про користувача для включення в повідомлення про помилку
        """
        try:
            from fastapi_sqlalchemy import db
            from sqlalchemy import text

            result = db.session.execute(
                text("SELECT id, login, email, fullname FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'login': result[1],
                    'email': result[2],
                    'fullname': result[3]
                }
                
        except Exception as e:
            logger.error(f"Помилка при отриманні інформації користувача {user_id}: {e}")
            
        return {'id': user_id, 'login': 'невідомо', 'email': None, 'fullname': None}
    
    async def send_message(self, chat_id: str, message: str) -> bool:
        """
        Відправити повідомлення в Telegram
        """
        if not self.enabled:
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            # Обрізаємо повідомлення якщо воно занадто довге (Telegram ліміт 4096 символів)
            if len(message) > 4000:
                message = message[:3950] + "...\n\n[ПОВІДОМЛЕННЯ ОБРІЗАНО]"
            
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Telegram повідомлення успішно відправлено в чат {chat_id}")
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(f"Помилка відправки Telegram повідомлення: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Винятак при відправці Telegram повідомлення: {e}")
            return False
    
    def send_error_notification(self, user_id: Optional[int], error_details: dict):
        """
        Відправити повідомлення про помилку адміністратору (синхронна версія)
        """
        if not self.enabled:
            return
        
        # Отримуємо інформацію про користувача якщо є
        user_info = None
        if user_id:
            user_info = self.get_user_info(user_id)
        
        message = self._format_error_message(error_details, user_info)
        
        # Запускаємо асинхронну функцію в event loop
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self.send_message(self.admin_chat_id, message))
        except RuntimeError:
            # Якщо немає активного event loop, створюємо новий
            asyncio.run(self.send_message(self.admin_chat_id, message))
    
    def _format_error_message(self, error_details: dict, user_info: Optional[dict] = None) -> str:
        """
        Форматувати повідомлення про помилку
        """
        message = "🚨 <b>Помилка в FinMan API</b>\n\n"
        
        # Інформація про користувача
        if user_info:
            message += f"<b>👤 Користувач:</b>\n"
            message += f"ID: {user_info['id']}\n"
            message += f"Логін: {user_info['login']}\n"
            if user_info.get('fullname'):
                message += f"Ім'я: {user_info['fullname']}\n"
            if user_info.get('email'):
                message += f"Email: {user_info['email']}\n"
            message += "\n"
        
        if error_details.get('url'):
            message += f"<b>🌐 URL:</b> {error_details['url']}\n"
        
        if error_details.get('method'):
            message += f"<b>📡 Метод:</b> {error_details['method']}\n"
        
        if error_details.get('error_type'):
            message += f"<b>⚠️ Тип помилки:</b> {error_details['error_type']}\n"
        
        if error_details.get('error_message'):
            message += f"<b>💬 Повідомлення:</b> {error_details['error_message']}\n\n"
        
        if error_details.get('traceback'):
            # Скорочуємо traceback для читабельності
            traceback_lines = error_details['traceback'].split('\n')
            if len(traceback_lines) > 20:
                traceback_short = '\n'.join(traceback_lines[-20:])  # Останні 20 рядків
                message += f"<b>📋 Traceback (останні рядки):</b>\n<pre>{traceback_short}</pre>"
            else:
                message += f"<b>📋 Traceback:</b>\n<pre>{error_details['traceback']}</pre>"
        
        message += f"\n<i>🕐 Час: {error_details.get('timestamp', 'невідомо')}</i>"
        
        return message

# Глобальний екземпляр
telegram_notifier = TelegramNotifier()