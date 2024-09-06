# Використовуємо офіційний образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файл залежностей (pyproject.toml) та Poetry Lock файл (якщо є) у контейнер
COPY pyproject.toml poetry.lock ./

# Встановлюємо Poetry та залежності
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root

# Копіюємо весь проєкт у контейнер
COPY . .

# Відкриваємо порт, який буде використовуватися FastAPI
EXPOSE 8000

# Команда для запуску додатку
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
