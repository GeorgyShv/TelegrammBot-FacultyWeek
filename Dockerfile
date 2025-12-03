# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Создаем необходимые директории для данных
RUN mkdir -p uploads images additional

# Устанавливаем переменные окружения по умолчанию (можно переопределить)
ENV PYTHONUNBUFFERED=1

# Запускаем бота
CMD ["python", "main.py"]

