#!/bin/bash

# Скрипт для створення дампу бази даних FinMan
# Використання: ./backup_db.sh [output_file]

set -e  # Вихід при помилці

# Завантажуємо змінні з .env файлу
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Помилка: файл .env не знайдено!"
    exit 1
fi

# Парсимо DATABASE_URI для отримання параметрів підключення
# Формат: mysql+pymysql://user:password@host:port/database
DB_URI="${DATABASE_URI}"

# Витягуємо компоненти з URI
DB_USER=$(echo $DB_URI | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASSWORD=$(echo $DB_URI | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo $DB_URI | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DB_URI | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DB_URI | sed -n 's/.*\/\([^?]*\).*/\1/p')

# Перевіряємо чи всі параметри витягнуто
if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ]; then
    echo "Помилка: не вдалося розпарсити DATABASE_URI"
    echo "Формат повинен бути: mysql+pymysql://user:password@host:port/database"
    exit 1
fi

# Використовуємо порт за замовчуванням, якщо не вказано
if [ -z "$DB_PORT" ]; then
    DB_PORT=3306
fi

# Генеруємо ім'я файлу дампу з датою та часом
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${1:-backup_finman_${TIMESTAMP}.sql}"

echo "=== Створення дампу бази даних FinMan ==="
echo "База даних: $DB_NAME"
echo "Хост: $DB_HOST:$DB_PORT"
echo "Користувач: $DB_USER"
echo "Файл дампу: $OUTPUT_FILE"
echo ""

# Створюємо дамп бази даних
echo "Починаємо створення дампу..."
mysqldump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --user="$DB_USER" \
    --password="$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --add-drop-table \
    --extended-insert \
    --quick \
    --lock-tables=false \
    "$DB_NAME" > "$OUTPUT_FILE"

# Перевіряємо чи файл створено
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "✅ Дамп успішно створено!"
    echo "📁 Файл: $OUTPUT_FILE"
    echo "📊 Розмір: $FILE_SIZE"
    echo ""
    echo "Для відновлення використайте:"
    echo "mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p $DB_NAME < $OUTPUT_FILE"
else
    echo "❌ Помилка: файл дампу не створено!"
    exit 1
fi
