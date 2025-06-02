# 💰 FinMan - Personal Finance Management System

> Комплексна система управління особистими та сімейними фінансами з підтримкою банківських інтеграцій та обліку комунальних послуг

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![Vue.js](https://img.shields.io/badge/Vue.js-3.1-brightgreen)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## 🚀 Можливості системи

### 💳 Банківські інтеграції
- **Автоматичний імпорт** виписок з CSV/Excel (Wise, Revolut, PrivatBank)
- **PDF парсинг** виписок (ПУМБ, Erste Bank)
- **Real-time API** інтеграція з MonoBank
- **Автоматична конвертація** валют через НБУ
- **Розпізнавання дублікатів** транзакцій

### 🏠 Управління комунальними послугами
- **Облік домогосподарств** - кілька адрес на користувача
- **Історія тарифів** з підтримкою абонентської плати
- **Автоматичний розрахунок** споживання та вартості
- **Багатотарифні системи** (день/ніч, подача/злив)
- **Звіти по періодах** та адресах

### 👥 Сімейні фінанси
- **Групи користувачів** з ролевою моделлю
- **Запрошення по коду** для членів сім'ї
- **Спільні категорії** витрат
- **Консолідовані звіти** по групі

### 📊 Аналітика та звітність
- **Категоризація витрат** з підкатегоріями
- **Статистика по періодах** (роки, місяці)
- **Валютні операції** з курсами НБУ
- **Експорт даних** у різних форматах

## 🏗 Архітектура проекту

```
finman_api/
├── 🔑 auth/                    # JWT автентифікація
├── 🌐 api/                     # REST API endpoints
│   ├── categories/             # Управління категоріями
│   ├── payments/              # Транзакції та платежі
│   ├── utilities/             # Комунальні послуги
│   ├── groups/                # Сімейні групи
│   ├── mono/                  # MonoBank інтеграція
│   └── core/                  # Банківські парсери
├── 🗄️ models/                  # SQLAlchemy моделі
├── 🔄 migrations/              # Alembic міграції БД
├── 📁 static/                  # Статичні файли
└── 🐳 docker-compose.yml       # Docker конфігурація
```

## 🛠 Встановлення та запуск

### Варіант 1: Docker (рекомендовано)

```bash
# Клонування репозиторію
git clone https://github.com/your-repo/finman_api.git
cd finman_api

# Налаштування змінних середовища
cp .env.example .env
# Відредагуйте .env файл

# Запуск через Docker Compose
docker compose up -d --build

# Система буде доступна на http://localhost:8090
```

### Варіант 2: Локальна розробка

```bash
# Створення віртуального середовища
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Встановлення залежностей
pip install -r requirements.txt

# Налаштування бази даних
alembic upgrade head

# Запуск сервера розробки
uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

## 🔄 Робота з міграціями БД

### Процес розробки

```bash
# 1. Внесіть зміни в моделі (models/models.py)

# 2. Згенеруйте міграцію
alembic revision --autogenerate -m "Add new feature"

# 3. ОБОВ'ЯЗКОВО перевірте згенерований файл
# Видаліть зайві операції з існуючими таблицями!

# 4. Протестуйте міграцію
alembic upgrade head
alembic downgrade -1  # Тест rollback
alembic upgrade head  # Повторне застосування

# 5. Закомітьте зміни
git add .
git commit -m "Add new feature [migrate]"
git push
```

### Важливі правила міграцій

> ⚠️ **ЗАВЖДИ перевіряйте згенеровані файли міграцій!**
> 
> Alembic може додавати зайві операції з існуючими індексами та таблицями.
> Видаляйте все, що НЕ стосується ваших змін.

```bash
# Поточний стан міграцій
alembic current

# Історія міграцій  
alembic history --verbose

# Позначити міграцію як виконану (без фактичного виконання)
alembic stamp head
```

## 🌐 API Endpoints

### 🔐 Автентифікація
```
POST   /api/auth/signup      # Реєстрація
POST   /api/auth/signin      # Вхід (отримання JWT)
POST   /api/auth/refresh     # Оновлення токена
```

### 💰 Фінанси
```
GET    /api/payments               # Список транзакцій
POST   /api/payments               # Створення транзакції
GET    /api/payments/period        # Аналітика по періодах
GET    /api/categories             # Категорії витрат
POST   /api/import                 # Імпорт банківських виписок
```

### 🏠 Комунальні послуги
```
# Адреси/домогосподарства
GET    /api/utilities/addresses              # Список адрес
POST   /api/utilities/addresses              # Створити адресу
PATCH  /api/utilities/addresses/{id}         # Оновити адресу

# Комунальні служби
GET    /api/utilities/services?address_id=1  # Служби адреси
POST   /api/utilities/services               # Створити службу

# Тарифи
GET    /api/utilities/tariffs?service_id=1   # Тарифи служби
POST   /api/utilities/tariffs                # Створити тариф

# Показники
GET    /api/utilities/readings?period=2024-01  # Показники за період
POST   /api/utilities/readings                  # Внести показник
```

### 👥 Групи та користувачі
```
GET    /api/groups                 # Мої групи
POST   /api/groups                 # Створити групу
GET    /api/invitations            # Запрошення до груп
```

## 🔌 Інтеграції з банками

### Підтримувані банки та формати

| Банк | Формат | Валюта | Особливості |
|------|---------|---------|-------------|
| **Wise** | CSV/Excel | USD, EUR | Міжнародні перекази |
| **Revolut** | CSV | Multi | Криптовалюти, біржа |
| **PrivatBank** | CSV/Excel | UAH | Найпопулярніший в Україні |
| **MonoBank** | API | UAH | Real-time синхронізація |
| **ПУМБ** | PDF | UAH | PDF парсинг виписок |
| **Erste Bank** | PDF | EUR → UAH | Автоконвертація валют |

### Приклад імпорту
```bash
curl -X POST "http://localhost:8090/api/import" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "mode=revolut" \
  -F "action=import" \
  -F "file=@statement.csv"
```

## 🏠 Комунальні послуги - Приклад використання

### 1. Створення домогосподарства
```json
POST /api/utilities/addresses
{
  "name": "Квартира",
  "address": "м. Київ, вул. Хрещатик, 1, кв. 15"
}
```

### 2. Додавання служби
```json
POST /api/utilities/services  
{
  "address_id": 1,
  "name": "Електроенергія",
  "unit": "кВт/год",
  "meter_number": "12345678"
}
```

### 3. Створення тарифів
```json
POST /api/utilities/tariffs
{
  "service_id": 1,
  "name": "Денний тариф", 
  "rate": 4.32,
  "subscription_fee": 0,
  "valid_from": "2024-01-01T00:00:00"
}

POST /api/utilities/tariffs
{
  "service_id": 1,
  "name": "Нічний тариф",
  "rate": 2.16, 
  "subscription_fee": 45.0,
  "valid_from": "2024-01-01T00:00:00"
}
```

### 4. Внесення показників
```json
POST /api/utilities/readings
{
  "address_id": 1,
  "service_id": 1,
  "period": "2024-01",
  "current_reading": 1250.5,
  "tariff_id": 1
}
```

**Результат:** Система автоматично розрахує:
- Споживання: `1250.5 - 1200.3 = 50.2 кВт`
- Сума: `(50.2 × 4.32) + 45.0 = 261.86 грн`

## 🚀 CI/CD та Деплой

### Автоматичний деплой

Система підтримує автоматичний деплой через Git hooks:

```bash
# Мітки для контролю міграцій
git commit -m "Add new feature [migrate]"    # Виконати міграції
git commit -m "Fix bug [nomigrate]"          # Пропустити міграції
```

### Бекап бази даних

```bash
# Створення бекапу
./backup_db.sh

# Тестування системи бекапу  
./test_backup.sh

# Відновлення з бекапу
mysql -h host -u user -p database < backup_file.sql
```

## 📊 Змінні середовища

Створіть файл `.env` з наступними параметрами:

```env
# База даних
DATABASE_URI=mysql+pymysql://user:password@host:3306/finman

# Безпека
SECRET_KEY=your_super_secret_jwt_key_here

# Зовнішні API (опціонально)  
MONOBANK_WEBHOOK_URL=https://your-domain.com/api/mono/webhook
NBU_API_URL=https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange

# Налаштування додатку
DEBUG=False
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend.com"]
```

## 🧪 Тестування

```bash
# Встановлення залежностей для тестування
pip install pytest pytest-asyncio httpx

# Запуск тестів
pytest tests/

# Тести з покриттям
pytest --cov=api tests/
```

## 📝 Швидкий старт для розробників

1. **Форкніть репозиторій**
2. **Створіть feature branch**: `git checkout -b feature/amazing-feature`
3. **Внесіть зміни** в моделі та API
4. **Згенеруйте міграцію**: `alembic revision --autogenerate -m "Add feature"`
5. **Перевірте міграцію** та видаліть зайві операції
6. **Протестуйте локально**: `alembic upgrade head`
7. **Закомітьте**: `git commit -m "Add feature [migrate]"`
8. **Створіть Pull Request**

## 🤝 Контрибуція

Ми відкриті для контрибуцій! Будь ласка:

1. Дотримуйтесь [PEP 8](https://www.python.org/dev/peps/pep-0008/)
2. Додавайте тести для нового функціоналу
3. Оновлюйте документацію
4. Перевіряйте міграції перед комітом

## 📄 Ліцензія

Цей проект розповсюджується під ліцензією MIT. Дивіться файл `LICENSE` для деталей.

## 💬 Підтримка

- 🐛 **Баги**: Створіть [issue](https://github.com/your-repo/finman_api/issues)
- 💡 **Ідеї**: Обговорення в [Discussions](https://github.com/your-repo/finman_api/discussions)  
- 📧 **Email**: support@finman.dev

---

<div align="center">

**Зроблено з ❤️ в Україні 🇺🇦**

[Документація](https://docs.finman.dev) • [Demo](https://demo.finman.dev) • [API](http://localhost:8090/docs)

</div>
