# MCP Server для MySQL доступу до FinMan бази даних

## Встановлення

```bash
npm install -g @modelcontextprotocol/server-mysql
```

## Конфігурація

Створіть файл ~/.mcp/servers.json з наступним вмістом:

```json
{
  "servers": {
    "finman-mysql": {
      "command": "mcp-server-mysql",
      "args": [],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "finman_user",
        "MYSQL_PASSWORD": "your_password",
        "MYSQL_DATABASE": "finman",
        "MCP_ALLOWED_OPERATIONS": "SELECT,SHOW"
      }
    }
  }
}
```

## Використання

Після налаштування сервер буде доступний для прямих SQL запитів до бази даних FinMan.
