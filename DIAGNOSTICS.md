# Диагностика проблем с Telegram ботом

## Быстрая проверка

### 1. Проверка статуса контейнера
```bash
docker compose ps
```

Контейнер должен быть в статусе `Up` (работает).

### 2. Просмотр логов
```bash
# Все логи
docker compose logs

# Последние 100 строк
docker compose logs --tail=100

# Логи в реальном времени
docker compose logs -f

# Только ошибки
docker compose logs 2>&1 | grep -i error
```

### 3. Проверка переменных окружения
```bash
# Проверить, что BOT_TOKEN установлен
docker compose exec telegram-bot env | grep BOT_TOKEN

# Или проверить файл .env
cat .env
```

### 4. Использование скрипта проверки
```bash
chmod +x check_bot.sh
./check_bot.sh
```

## Частые проблемы и решения

### Проблема: Контейнер не запускается

**Решение:**
1. Проверьте логи: `docker compose logs`
2. Убедитесь, что файл `.env` существует и содержит `BOT_TOKEN=ваш_токен`
3. Проверьте, что порты не заняты
4. Пересоберите образ: `docker compose build --no-cache`

### Проблема: Бот не отвечает на сообщения

**Проверьте:**
1. Контейнер запущен: `docker compose ps`
2. Нет ошибок в логах: `docker compose logs --tail=50`
3. Токен бота правильный (проверьте у @BotFather)
4. Бот не заблокирован в Telegram

**Решение:**
```bash
# Перезапустите бота
docker compose restart

# Или пересоздайте контейнер
docker compose down
docker compose up -d
```

### Проблема: Ошибка "BOT_TOKEN environment variable is not set"

**Решение:**
1. Создайте файл `.env` в корне проекта:
   ```
   BOT_TOKEN=ваш_токен_бота
   ```
2. Перезапустите контейнер:
   ```bash
   docker compose down
   docker compose up -d
   ```

### Проблема: Ошибки при чтении JSON файлов

**Решение:**
1. Убедитесь, что файлы существуют и имеют правильный формат JSON
2. Проверьте права доступа:
   ```bash
   ls -la *.json
   ```
3. Если файлы отсутствуют, они будут созданы автоматически при первом запуске

### Проблема: Файлы не сохраняются между перезапусками

**Решение:**
1. Проверьте, что volumes правильно смонтированы в `docker-compose.yml`
2. Убедитесь, что файлы не находятся в `.dockerignore`
3. Проверьте права доступа к файлам

## Команды для отладки

```bash
# Войти в контейнер
docker compose exec telegram-bot bash

# Проверить переменные окружения внутри контейнера
docker compose exec telegram-bot env

# Проверить файлы внутри контейнера
docker compose exec telegram-bot ls -la /app

# Проверить процесс Python
docker compose exec telegram-bot ps aux

# Перезапустить бота
docker compose restart telegram-bot

# Остановить и удалить контейнер (данные сохранятся)
docker compose down

# Полная пересборка
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Проверка работы бота

1. Откройте Telegram и найдите вашего бота
2. Отправьте команду `/start`
3. Проверьте логи: `docker compose logs -f`
4. Если бот не отвечает, проверьте логи на наличие ошибок

## Логирование

Бот теперь выводит подробные логи при запуске:
- ✓ - успешная операция
- ⚠ - предупреждение
- ❌ - ошибка

Все ошибки также логируются с полным traceback для упрощения отладки.

