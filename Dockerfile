FROM python:3.10-slim

WORKDIR /app

# Встановлюємо залежності перед копіюванням коду
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код в контейнер
COPY . .

# Відкриваємо порт
EXPOSE 8090

# Запускаємо FastAPI додаток через Gunicorn
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8090", "-w", "2", "--timeout", "120"]