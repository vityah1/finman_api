#!/usr/bin/env python3
"""
Простий тест для Telegram API без залежностей від проекту
"""
import asyncio
import aiohttp
import logging

# Налаштування
BOT_TOKEN = '461986981:AAGHyTw5Na_o_9ln1GXjPV5zhwU6mR52Svc'
CHAT_ID = '190722186'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_send_message():
    """
    Тест відправки повідомлення
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = """🚨 <b>ТЕСТ: Помилка в FinMan API</b>

<b>👤 Користувач:</b>
ID: 1
Логін: test_user

<b>🌐 URL:</b> /api/utilities/readings
<b>📡 Метод:</b> POST
<b>⚠️ Тип помилки:</b> TestError
<b>💬 Повідомлення:</b> Це тестове повідомлення про помилку

<b>📋 Traceback:</b>
<pre>
Traceback (most recent call last):
  File "test.py", line 1, in test_function
    raise Exception("Test error")
Exception: Test error
</pre>

<i>🕐 Час: 2025-07-12 15:30:00</i>"""
    
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Повідомлення успішно відправлено: {result}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Помилка {response.status}: {error_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Винятак при відправці: {e}")
        return False

async def main():
    print("🔄 Тестування Telegram API...")
    success = await test_send_message()
    
    if success:
        print("✅ Тест успішний! Повідомлення відправлено в Telegram")
    else:
        print("❌ Тест провалився")

if __name__ == "__main__":
    asyncio.run(main())