# Посібник з встановлення та налаштування FinMan 1.0

## Огляд

FinMan — це повноцінне рішення для управління особистими та сімейними фінансами, що складається з:
- RESTful API бекенду на Flask з JWT автентифікацією
- Сучасного фронтенду на Vue.js 3.1
- Підтримки Docker для простого розгортання

## Системні вимоги

- Python 3.8+
- MySQL або MariaDB
- NodeJS 14+ (для розробки фронтенду)
- Docker та Docker Compose (опціонально)

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
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. **Запустіть сервер в режимі розробки:**
   ```bash
   python runserver.py
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
   ExecStart=/bin/bash -c "source /path/to/finman_api/venv/bin/activate && gunicorn -w 2 -b 127.0.0.1:8090 app:app"
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

### Варіант 4: Налаштування на shared хостингу з Apache

1. **Виконайте кроки 1-4 з Варіанту 2**

2. **Відредагуйте .htaccess файл:**
   ```
   RewriteEngine On
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteRule ^(.*)$ /cgi-bin/main.py/$1 [L]
   ```

3. **Переконайтеся, що main.py має правильний шлях до вашого віртуального середовища Python:**
   ```python
   #!/path/to/your/venv/bin/python3
   from wsgiref.handlers import CGIHandler
   from app import app
   CGIHandler().run(app)
   ```

## Керування міграціями бази даних

Для роботи з існуючою базою даних:

```bash
# Створення початкової міграції на основі існуючої бази даних
flask db revision --autogenerate -m "Initial migration"

# Оновлення бази даних до останньої версії
flask db upgrade
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

- `/app` - Конфігурація та ініціалізація Flask
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
- **Проблеми з міграціями**: Запустіть `flask db current` для перевірки поточного стану міграцій
- **Помилки CORS**: Переконайтеся, що ваш фронтенд має доступ до API через налаштування CORS

## Розробка фронтенду

```bash
cd frontend
npm install
npm run serve  # Для розробки
npm run build  # Для створення production-версії
```

Дякуємо за використання FinMan! Якщо виникнуть питання, створіть issue на GitHub.
