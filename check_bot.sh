#!/bin/bash

# Скрипт для проверки статуса бота

echo "=========================================="
echo "Проверка статуса Telegram бота"
echo "=========================================="
echo ""

# Проверка статуса контейнера
echo "1. Статус контейнера:"
docker compose ps
echo ""

# Проверка логов (последние 50 строк)
echo "2. Последние логи (50 строк):"
echo "----------------------------------------"
docker compose logs --tail=50
echo ""

# Проверка переменных окружения
echo "3. Проверка переменных окружения:"
if [ -f .env ]; then
    echo "✓ Файл .env найден"
    if grep -q "BOT_TOKEN" .env; then
        TOKEN_LENGTH=$(grep "BOT_TOKEN" .env | cut -d'=' -f2 | wc -c)
        if [ "$TOKEN_LENGTH" -gt 10 ]; then
            echo "✓ BOT_TOKEN установлен (длина: $((TOKEN_LENGTH-1)) символов)"
        else
            echo "⚠ BOT_TOKEN слишком короткий или не установлен"
        fi
    else
        echo "❌ BOT_TOKEN не найден в .env"
    fi
else
    echo "⚠ Файл .env не найден"
    echo "   Создайте файл .env с переменной BOT_TOKEN=ваш_токен"
fi
echo ""

# Проверка файлов данных
echo "4. Проверка файлов данных:"
for file in users.json tasks.json market.json admins.json submissions.json; do
    if [ -f "$file" ]; then
        echo "✓ $file существует"
    else
        echo "⚠ $file не найден (будет создан автоматически)"
    fi
done
echo ""

# Проверка директорий
echo "5. Проверка директорий:"
for dir in uploads images additional; do
    if [ -d "$dir" ]; then
        echo "✓ $dir существует"
    else
        echo "⚠ $dir не найден (будет создан автоматически)"
    fi
done
echo ""

# Проверка подключения к Telegram API
echo "6. Проверка работы бота:"
CONTAINER_NAME="telegram-faculty-bot"
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "✓ Контейнер запущен"
    # Проверяем, есть ли ошибки в логах
    ERROR_COUNT=$(docker compose logs --tail=100 2>&1 | grep -i "error\|exception\|traceback" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "⚠ Найдено $ERROR_COUNT ошибок в логах"
        echo "   Проверьте логи: docker compose logs -f"
    else
        echo "✓ Ошибок в последних логах не обнаружено"
    fi
else
    echo "❌ Контейнер не запущен"
    echo "   Запустите: docker compose up -d"
fi
echo ""

echo "=========================================="
echo "Для просмотра логов в реальном времени:"
echo "  docker compose logs -f"
echo ""
echo "Для перезапуска бота:"
echo "  docker compose restart"
echo "=========================================="

