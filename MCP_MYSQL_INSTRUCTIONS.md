# MCP MySQL Server для FinMan

## Для встановлення та використання MCP MySQL сервера:

1. **Встановіть MCP MySQL сервер глобально:**
   ```bash
   npm install -g @modelcontextprotocol/server-mysql
   ```

2. **Додайте конфігурацію в Claude Desktop:**
   
   Відкрийте файл конфігурації Claude Desktop:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

3. **Додайте наступну конфігурацію:**
   ```json
   {
     "mcpServers": {
       "finman-mysql": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-mysql"],
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

4. **Перезапустіть Claude Desktop**

Після цього в Claude з'явиться можливість виконувати прямі SQL запити до бази даних FinMan.
