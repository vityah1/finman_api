# Створення власного MCP сервера для MySQL

Оскільки офіційний `@modelcontextprotocol/server-mysql` не існує, створимо власний простий MCP сервер для MySQL.

## Файл: mcp-mysql-server.js

```javascript
const mysql = require('mysql2/promise');

// Конфігурація з'єднання
const config = {
  host: process.env.MYSQL_HOST || '127.0.0.1',
  port: process.env.MYSQL_PORT || 3306,
  user: process.env.MYSQL_USER || 'finman',
  password: process.env.MYSQL_PASSWORD || '6AbR5VNDrj2kQqfB7ryL',
  database: process.env.MYSQL_DATABASE || 'finman'
};

// Створення пулу з'єднань
let pool;

async function initialize() {
  pool = mysql.createPool(config);
  console.log('MySQL MCP Server initialized');
}

async function executeQuery(query, params = []) {
  try {
    const [rows] = await pool.execute(query, params);
    return { success: true, data: rows };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// MCP Server implementation
async function handleRequest(request) {
  const { method, params } = request;
  
  switch (method) {
    case 'query':
      return await executeQuery(params.sql, params.values || []);
    case 'tables':
      return await executeQuery('SHOW TABLES');
    case 'describe':
      return await executeQuery(`DESCRIBE ${params.table}`);
    default:
      return { error: 'Unknown method' };
  }
}

// Ініціалізація
initialize().catch(console.error);

module.exports = { handleRequest };
```

## Встановлення:

1. Створіть директорію для MCP сервера:
```bash
mkdir ~/mcp-mysql-finman
cd ~/mcp-mysql-finman
```

2. Ініціалізуйте npm проект:
```bash
npm init -y
npm install mysql2
```

3. Створіть файл `index.js` з кодом вище

4. Оновіть конфігурацію Claude:
```json
{
  "mcpServers": {
    "finman-mysql": {
      "command": "node",
      "args": ["C:/Users/vholo/mcp-mysql-finman/index.js"],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "finman",
        "MYSQL_PASSWORD": "6AbR5VNDrj2kQqfB7ryL",
        "MYSQL_DATABASE": "finman"
      }
    }
  }
}
```
