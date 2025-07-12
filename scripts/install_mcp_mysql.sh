#!/bin/bash

# Встановлення MCP MySQL сервера для FinMan

echo "Встановлення MCP MySQL сервера..."

# Встановлюємо глобально MCP MySQL сервер
npm install -g @modelcontextprotocol/server-mysql

# Створюємо директорію для конфігурації якщо не існує
mkdir -p ~/.mcp

# Створюємо конфігураційний файл
cat > ~/.mcp/servers.json << 'EOF'
{
  "servers": {
    "finman-mysql": {
      "command": "mcp-server-mysql",
      "args": [],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "finman",
        "MYSQL_PASSWORD": "6AbR5VNDrj2kQqfB7ryL",
        "MYSQL_DATABASE": "finman",
        "MCP_ALLOWED_OPERATIONS": "SELECT,SHOW,DESCRIBE"
      }
    }
  }
}
EOF

echo "✅ MCP MySQL сервер встановлено!"
echo "⚠️  Не забудьте оновити пароль в файлі ~/.mcp/servers.json"
