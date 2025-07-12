# Виправлення проблем CI/CD FinMan

## 🚨 Проблема
```
FAILED: No 'script_location' key found in configuration.
```

## ✅ Виправлення

### 1. Створено правильний alembic.ini в корені проекту
- Файл містить секцію `[alembic]` з `script_location = migrations`
- Налаштоване логування

### 2. Створено міграцію для нових таблиць
- `migrations/versions/2025_06_01_2030_add_utility_tables.py`
- Додає таблиці для комунальних служб:
  - `utility_addresses` - адреси/домогосподарства
  - `utility_services` - комунальні служби
  - `utility_tariffs` - тарифи
  - `utility_readings` - показники

### 3. Створено систему бекапу БД
- `backup_db.sh` - основний скрипт бекапу
- `test_backup.sh` - тестування системи бекапу
- Автоматично парсить .env для отримання параметрів підключення

## 🛠 Використання

### Створення бекапу БД:
```bash
./backup_db.sh                    # Автоматична назва файлу
./backup_db.sh my_backup.sql      # Вказана назва файлу
```

### Тестування бекапу:
```bash
./test_backup.sh
```

### Запуск міграцій:
```bash
# В Docker контейнері
docker exec finman_api alembic upgrade head

# Локально з віртуальним середовищем
source .venv/bin/activate
alembic upgrade head
```

## 📋 Нові API ендпоінти

### Адреси:
- `GET /api/utilities/addresses` - список адрес
- `POST /api/utilities/addresses` - створити адресу
- `PATCH /api/utilities/addresses/{id}` - оновити
- `DELETE /api/utilities/addresses/{id}` - видалити

### Служби:
- `GET /api/utilities/services?address_id=1` - служби адреси
- `POST /api/utilities/services` - створити службу
- `PATCH /api/utilities/services/{id}` - оновити
- `DELETE /api/utilities/services/{id}` - видалити

### Тарифи:
- `GET /api/utilities/tariffs?service_id=1` - тарифи служби
- `POST /api/utilities/tariffs` - створити тариф
- `PATCH /api/utilities/tariffs/{id}` - оновити
- `DELETE /api/utilities/tariffs/{id}` - видалити

### Показники:
- `GET /api/utilities/readings?address_id=1&period=2024-01` - показники
- `POST /api/utilities/readings` - внести показник
- `PATCH /api/utilities/readings/{id}` - оновити
- `DELETE /api/utilities/readings/{id}` - видалити

## 🎯 Логіка роботи

1. **Створіть адресу** (Квартира, Дача)
2. **Додайте служби до адреси** (Електроенергія, Газ, Вода)
3. **Створіть тарифи для служб** (можна кілька на службу)
4. **Вносьте показники** - система автоматично розрахує споживання та вартість

## 🔧 Коміт для деплою
```bash
git add .
git commit -m "Fix CI/CD: add alembic.ini and utility tables [migrate]"
git push origin main
```

Мітка `[migrate]` автоматично запустить міграції при деплої.
