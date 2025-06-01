#!/bin/bash

# Скрипт для тестування бекапу БД FinMan
# Використання: ./test_backup.sh

echo "=== Тестування системи бекапу FinMan ==="

# Перевіряємо чи існує .env файл
if [ ! -f .env ]; then
    echo "❌ Файл .env не знайдено!"
    exit 1
fi

# Перевіряємо чи mysqldump доступний
if ! command -v mysqldump &> /dev/null; then
    echo "❌ mysqldump не встановлено!"
    echo "Встановіть: sudo apt-get install mysql-client"
    exit 1
fi

# Перевіряємо чи backup_db.sh виконуваний
if [ ! -x backup_db.sh ]; then
    echo "❌ backup_db.sh не виконуваний!"
    echo "Виконайте: chmod +x backup_db.sh"
    exit 1
fi

echo "✅ Всі залежності перевірені"
echo ""

# Тестуємо створення бекапу
echo "🔄 Тестуємо створення бекапу..."
TEST_BACKUP_FILE="test_backup_$(date +%Y%m%d_%H%M%S).sql"

if ./backup_db.sh "$TEST_BACKUP_FILE"; then
    echo "✅ Бекап успішно створено!"
    
    # Перевіряємо розмір файлу
    if [ -f "$TEST_BACKUP_FILE" ]; then
        SIZE=$(du -h "$TEST_BACKUP_FILE" | cut -f1)
        echo "📊 Розмір файлу: $SIZE"
        
        # Видаляємо тестовий файл
        read -p "Видалити тестовий файл $TEST_BACKUP_FILE? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm "$TEST_BACKUP_FILE"
            echo "🗑️ Тестовий файл видалено"
        fi
    fi
else
    echo "❌ Помилка створення бекапу!"
    exit 1
fi

echo ""
echo "✅ Система бекапу працює правильно!"
