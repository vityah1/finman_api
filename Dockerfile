FROM python:3.10-slim

WORKDIR /app

# Встановлюємо залежності перед копіюванням коду
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код в контейнер
COPY . .

# Відкриваємо порт
EXPOSE 8090

# Запускаємо FastAPI додаток напряму через Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]