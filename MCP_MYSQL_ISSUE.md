# Виправлення MCP MySQL Server

## Проблема
Пакет `@modelcontextprotocol/server-mysql` не існує в npm реєстрі.

## Альтернативні рішення:

### 1. Використати sqlite3 MCP сервер з MySQL адаптером
```json
{
  "mcpServers": {
    "finman-db": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite"
      ],
      "env": {
        "DATABASE_PATH": "path/to/database.db"
      }
    }
  }
}
```

### 2. Створити власний простий MCP сервер для MySQL
Необхідно створити простий Node.js скрипт що буде працювати як MCP сервер.

### 3. Використати існуючі SQL MCP сервери
- Перевірити офіційний список MCP серверів на https://modelcontextprotocol.io/
- Пошукати community реалізації

## Поточний статус
На даний момент прямий доступ до MySQL через MCP не налаштований через відсутність відповідного пакета.
