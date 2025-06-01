# Посібник з встановлення та налаштування FinMan 1.0

## Огляд

FinMan — це повноцінне рішення для управління особистими та сімейними фінансами, що складається з:

- RESTful API бекенду на FastAPI з JWT автентифікацією and SWAGGER
- Сучасного фронтенду на Vue.js 3.1, Orval
- Підтримки Docker для простого розгортання

## Системні вимоги

- Python 3.10+
- MySQL
- Docker та Docker Compose (опціонально)

## Можливості

### Імпорт банківських виписок

- Імпорту виписок з Revolut, Wise, PrivatBank
- Отримання онлайн транзакцій від MonoBank
- Імпорт транзакцій MonoBank по АПІ

### Внесення транзакцій


## Варіанти встановлення

Виберіть один із способів встановлення та запуску:

### Варіант 1: Встановлення через Docker (рекомендовано)

1. **Клонуйте репозиторій:**
   ```bash
   git clone https://github.com/your-repo/finman_api.git
   cd finman_api
   ```

2. **Створіть файл .env:**
   ```
   DATABASE_URI=mysql+pymysql://user:password@db:3306/finman
   SECRET_KEY=your_super_secret_string
   ```

3. **Запустіть через Docker Compose:**
   ```bash
   docker compose up -d
   ```
   
   Система автоматично виконає міграцію бази даних та запустить сервер на порту 8090.

### Варіант 2: Локальне встановлення для розробки

1. **Клонуйте репозиторій:**
   ```bash
   git clone https://github.com/your-repo/finman_api.git
   cd finman_api
   ```

2. **Створіть віртуальне середовище та встановіть залежності:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Створіть файл .env:**
   ```
   DATABASE_URI=mysql+pymysql://user:password@localhost:3306/finman
   SECRET_KEY=your_super_secret_string
   ```

4. **Ініціалізуйте та налаштуйте базу даних:**
   ```bash
   python -c "from mydb import db; db.create_all()"
   ```

5. **Запустіть сервер в режимі розробки:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8090
   ```

### Варіант 3: Встановлення як системний сервіс (Linux)

1. **Виконайте кроки 1-4 з Варіанту 2**

2. **Створіть файл сервісу:**
   ```bash
   sudo nano /etc/systemd/system/finman.service
   ```

3. **Додайте наступний вміст (замініть шляхи на актуальні):**
   ```
   [Unit]
   Description=Finman Financial Manager
   After=network.target

   [Service]
   User=finman
   Group=finman
   WorkingDirectory=/path/to/finman_api
   ExecStart=/bin/bash -c "source /path/to/finman_api/venv/bin/activate && gunicorn -w 2 -b 127.0.0.1:8090 main:app --timeout 120"
   Restart=always

   [Install]
   WantedBy=default.target
   ```

4. **Запустіть та увімкніть сервіс:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start finman
   sudo systemctl enable finman
   ```

## Керування міграціями бази даних

Для роботи з існуючою базою даних використовуйте Alembic:

```bash
# Ініціалізація Alembic (якщо ще не ініціалізовано)
alembic init migrations

# Створення початкової міграції на основі існуючої бази даних
alembic revision --autogenerate -m "Initial migration"

# Оновлення бази даних до останньої версії
alembic upgrade head 
```

### Налаштування вибіркової міграції таблиць

Щоб виключити певні таблиці з процесу міграції, відредагуйте файл `migrations/env.py`:

1. **Додайте функцію фільтрації:**
   ```python
   def include_object(object, name: str, type_, reflected, compare_to):
       """
       Визначає, чи включати таблицю/колонку в міграцію
       """
       if type_ == 'table' and (name.startswith('_') or object.info.get("skip_autogenerate", False)):
           return False
       elif type_ == "column" and object.info.get("skip_autogenerate", False):
           return False
       return True
   ```

2. **Додайте параметр до налаштувань контексту:**
   ```python
   context.configure(
       connection=connection,
       target_metadata=get_metadata(),
       include_object=include_object,
       # інші налаштування...
   )
   ```

## Структура проекту

- `/api` - Ендпоінти API
- `/models` - Моделі даних SQLAlchemy
- `/auth` - Логіка аутентифікації та авторизації
- `/migrations` - Файли міграції бази даних
- `/scripts` - Корисні скрипти (імпорт валют, тощо)

## Додаткові налаштування

### Налаштування Telegram-повідомлень

1. Отримайте токен бота через BotFather
2. Додайте налаштування в розділі Профіль -> Налаштування

### Налаштування MonoBank

1. Отримайте токен в додатку MonoBank
2. Створіть нового MonoBank користувача в системі
3. Налаштуйте webhook для автоматичного імпорту транзакцій

## Вирішення проблем

- **Помилка підключення до бази даних**: Перевірте параметри у DATABASE_URI та доступність сервера бази даних
- **Проблеми з міграціями**: Запустіть `alembic current` для перевірки поточного стану міграцій
- **Помилки CORS**: Переконайтеся, що ваш фронтенд має доступ до API через налаштування CORS

Дякуємо за використання FinMan! Якщо виникнуть питання, створіть issue на GitHub.
