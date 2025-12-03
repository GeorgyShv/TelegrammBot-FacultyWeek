import json
import os
import asyncio
from telegram.error import TelegramError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault, BotCommandScopeChat, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Пути к файлам
USERS_FILE = "users.json"
MARKET_FILE = "market.json"
TASKS_FILE = "tasks.json"
ADMINS_FILE = "admins.json"
SUBMISSIONS_FILE = "submissions.json"

# Глобальные переменные
users = {}
market = []
tasks = {}
admins = []
submissions = {}


# Загрузка данных администраторов
def load_admins():
    global admins
    try:
        with open(ADMINS_FILE, "r") as file:
            admins = json.load(file)
    except FileNotFoundError:
        admins = []


# Сохранение данных администраторов
def save_admins():
    with open(ADMINS_FILE, "w") as file:
        json.dump(admins, file, indent=4)


# Проверка администратора
def is_admin(user_id):
    return user_id in admins


# Команда для добавления нового администратора
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if is_admin(user_id):
        try:
            new_admin_id = int(context.args[0])
            if new_admin_id not in admins:
                admins.append(new_admin_id)
                save_admins()
                await set_bot_commands(context.application)  # Обновляем команды
                await update.message.reply_text(f"Администратор с ID {new_admin_id} успешно добавлен.")
            else:
                await update.message.reply_text("Этот пользователь уже является администратором.")
        except (IndexError, ValueError):
            await update.message.reply_text("Используйте команду в формате: /addadmin <ID пользователя>")
    else:
        await update.message.reply_text("У вас нет прав администратора.")


# Команда для удаления администратора
async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if is_admin(user_id):
        try:
            admin_id_to_remove = int(context.args[0])  # Получаем ID администратора для удаления
            if admin_id_to_remove in admins:
                admins.remove(admin_id_to_remove)
                save_admins()  # Сохраняем изменения
                await update.message.reply_text(f"Администратор с ID {admin_id_to_remove} успешно удален.")
            else:
                await update.message.reply_text("Этот пользователь не является администратором.")
        except (IndexError, ValueError):
            await update.message.reply_text("Используйте команду в формате: /removeadmin <ID пользователя>")
    else:
        await update.message.reply_text("У вас нет прав администратора.")


# Загрузка данных из JSON
def load_data():
    global users, market, tasks, submissions
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            users = json.load(file)
    except FileNotFoundError:
        users = {}
        print(f"Файл {USERS_FILE} не найден, создан пустой словарь")
    except json.JSONDecodeError as e:
        users = {}
        print(f"Ошибка парсинга {USERS_FILE}: {e}, создан пустой словарь")

    try:
        with open(MARKET_FILE, "r", encoding="utf-8") as file:
            market = json.load(file)
    except FileNotFoundError:
        market = []
        print(f"Файл {MARKET_FILE} не найден, создан пустой список")
    except json.JSONDecodeError as e:
        market = []
        print(f"Ошибка парсинга {MARKET_FILE}: {e}, создан пустой список")

    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as file:
            tasks = json.load(file)
    except FileNotFoundError:
        tasks = {}
        print(f"Файл {TASKS_FILE} не найден, создан пустой словарь")
    except json.JSONDecodeError as e:
        tasks = {}
        print(f"Ошибка парсинга {TASKS_FILE}: {e}, создан пустой словарь")

    try:
        with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as file:
            submissions = json.load(file)
    except FileNotFoundError:
        submissions = {}
        print(f"Файл {SUBMISSIONS_FILE} не найден, создан пустой словарь")
    except json.JSONDecodeError as e:
        submissions = {}
        print(f"Ошибка парсинга {SUBMISSIONS_FILE}: {e}, создан пустой словарь")


# Сохранение данных в JSON
def save_data():
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)
    with open(MARKET_FILE, "w", encoding="utf-8") as file:
        json.dump(market, file, indent=4)
    with open(TASKS_FILE, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=4)
    with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(submissions, file, indent=4)


# Проверка администратора
def is_admin(user_id):
    return user_id in admins


def load_user_data():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)


# Проверка блокировки пользователя
async def check_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Загружаем данные пользователей
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except Exception as e:
        print(f"Ошибка чтения users.json: {e}")
        return

    # Проверяем, заблокирован ли пользователь
    if user_id in users and users[user_id].get("blocked", False):
        await update.message.reply_text("Вы заблокированы администратором. Доступ к боту ограничен.")
        return False  # Прерываем обработку команды
    return True


async def command_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, handler):
    if not await check_blocked(update, context):  # Проверяем статус блокировки
        return
    await handler(update, context)  # Выполняем основной обработчик


# Пользовательские команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    photo_path = "additional/HelloMessage.jpg"  # Замените на путь к вашему изображению

    if chat_id in users:
        await update.message.reply_text("Вы уже зарегистрированы!")
    else:
        # Отправляем фотографию
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(photo_path, 'rb'),  # Открываем файл для отправки
            caption=(
                "Это филфак, и ты не прогадал!\n"
                "\n"
                "На связи факультет русской филологии и национальной культуры РГУ имени С.А. Есенина."
                "\n"
                "🦉 С помощью этого бота ты сможешь копить баллы за пройденные мероприятия и задания. "
                "И в конце тебя ждут приятные призы!\n"
                "\n"
                "Филфак однажды — филфак навсегда ❤️\n"
                "\n"
                "Телеграмм канал факультета: https://t.me/rsu_frfnk"
            )
        )

        # Отправляем сообщение с инструкцией для регистрации
        await update.message.reply_text(
            "Для регистрации введите ФИО (данные отправятся на модерацию)"
        )

        # Устанавливаем флаг для регистрации
        context.user_data['registration'] = True


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Это бот для участников конкурса. Доступные команды:\n"
        "/wallet - посмотреть ваш баланс\n"
        "/tasks - список заданий\n"
        "/market - магазин наград\n"
        "/purchased - купленные призы\n"
        "/help - информация о боте"
    )


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = users.get(chat_id)

    if not user:
        await update.message.reply_text("Вы не зарегистрированы!")
        return

    if not user.get("approved"):
        await update.message.reply_text("Ваша регистрация не подтверждена администраторами!")
        return

    if not tasks:
        await update.message.reply_text("Список заданий пуст.")
        return

    for task_id, task in tasks.items():
        requires = task.get("requires", "both")
        requirements_text = {
            "text": "Требуется текст",
            "photo": "Требуется фото",
            "both": "Требуется текст и фото"
        }[requires]

        await update.message.reply_text(
            text=(
                f"Название: {task['title']}\n"
                f"Описание: {task['description']}\n"
                f"Награда: {task['reward']} баллов\n"
                f"Требования: {requirements_text}\n"
                f"Для выполнения задания отправьте команду: /task_{task_id}"
            )
        )


def task_command_handler(task_id):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        user = users.get(chat_id)

        # Проверяем регистрацию пользователя
        if not user:
            await update.message.reply_text("Вы не зарегистрированы!")
            return

        # Проверяем подтверждение регистрации
        if not user.get("approved"):
            await update.message.reply_text("Ваша регистрация не подтверждена администраторами!")
            return

        # Проверяем существование задания
        task = tasks.get(str(task_id))
        if not task:
            await update.message.reply_text("Задание не найдено.")
            return

        # Сохраняем текущее задание пользователя
        user["current_task"] = task_id
        save_json("users.json", users)

        context.user_data["task_action"] = "perform_task"

        # Устанавливаем task_id в context.user_data
        context.user_data['current_task'] = task_id

        # Формируем сообщение с учётом требований задания
        requires = task.get("requires", "both")
        requirements_text = {
            "text": "Пожалуйста, отправьте текст выполнения задания.",
            "photo": "Пожалуйста, отправьте фото выполнения задания.",
            "both": "Пожалуйста, отправьте текст и фото выполнения задания."
        }[requires]

        await update.message.reply_text(
            f"Задание '{task['title']}' выбрано.\n"
            f"{requirements_text}"
        )

    return handler


def load_json(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_json(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


async def handle_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = users.get(chat_id)

    if not user:
        await update.message.reply_text("Вы не зарегистрированы!")
        return

    # Получаем task_id из context.user_data
    task_id = context.user_data.get("current_task")
    if not task_id:
        await update.message.reply_text("Вы не выбрали задание для выполнения. Воспользуйтесь командой типа /task_1.")
        return

    task = tasks.get(str(task_id))
    if not task:
        await update.message.reply_text("Задание не найдено.")
        return

    # Проверка требований задания
    requires = task.get("requires", "both")
    has_text = bool(update.message.caption)  # Проверяем caption (текст, связанный с фото)
    has_photo = bool(update.message.photo)  # Проверяем, есть ли фото

    # Проверка условий, что требует задание
    if requires == "photo" and not has_photo:
        await update.message.reply_text("Это задание требует фото. Пожалуйста, отправьте фотографию.")
        return

    if requires == "text" and not has_text:
        await update.message.reply_text("Это задание требует текст. Пожалуйста, отправьте описание.")
        return

    if requires == "both" and (not has_text or not has_photo):
        await update.message.reply_text("Это задание требует текст и фото. Пожалуйста, отправьте оба элемента.")
        return

    # Сохраняем фото (если есть)
    save_path = None
    if has_photo:
        photo = update.message.photo[-1]  # Получаем самое лучшее качество фото
        file = await photo.get_file()
        save_path = os.path.join("uploads", f"user_{chat_id}_task_{task_id}.jpg")
        await file.download_to_drive(save_path)

    # Получаем текст из caption (если он есть)
    text = update.message.caption if update.message.caption else None

    # Сохраняем выполнение в submissions.json
    submissions = load_json("submissions.json")
    if chat_id not in submissions:
        submissions[chat_id] = []

    submissions[chat_id].append({
        "task_id": task_id,
        "photo_path": save_path,
        "text": text,
        "status": "pending",
        "admin_comment": None
    })
    save_json("submissions.json", submissions)

    # Сбрасываем текущее задание
    user["current_task"] = None
    save_json("users.json", users)

    # Уведомляем пользователя
    await update.message.reply_text(
        "Ваше выполнение задания отправлено на проверку администраторам!"
    )


async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = users.get(chat_id)
    if not user:
        await update.message.reply_text("Вы не зарегистрированы!")
        return
    elif not user.get("approved"):
        await update.message.reply_text("Ваша регистрация не подтверждена администраторами!")
        return
    elif user:
        load_data()
        await update.message.reply_text(
            f"ФИО: {user['full_name']}\nID: {user['id']}\nВаш баланс: {user['balance']} баллов."
        )


async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = users.get(chat_id)
    if not user:
        await update.message.reply_text("Вы не зарегистрированы!")
        return
    elif not user.get("approved"):
        await update.message.reply_text("Ваша регистрация не подтверждена администраторами!")
        return

    context.user_data['market_index'] = 0
    await show_market_item(update, context)


async def purchased_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = users.get(chat_id)
    if not user:
        await update.message.reply_text("Вы не зарегистрированы!")
        return
    elif not user.get("approved"):
        await update.message.reply_text("Ваша регистрация не подтверждена администраторами!")
        return

    purchased_items = user.get("purchased", [])
    if not purchased_items:
        await update.message.reply_text("У вас еще нет купленных товаров.")
        return

    # Формируем текст для списка купленных товаров
    purchased_list = "Ваши купленные товары:\n"
    for item in purchased_items:
        purchased_list += f"- {item}\n"

    await update.message.reply_text(purchased_list)


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if context.user_data.get('registration'):
        full_name = update.message.text
        users[chat_id] = {"id": chat_id, "full_name": full_name, "balance": 0, "completed_tasks": [], "purchased": [], "approved": False, "blocked": False}
        context.user_data['registration'] = False
        save_data()

        # Уведомление администраторам
        for admin_id in admins:
            keyboard = [
                [
                    InlineKeyboardButton("Подтвердить", callback_data=f"prinyat_{chat_id}"),
                    InlineKeyboardButton("Отклонить", callback_data=f"decline_{chat_id}")
                ]
            ]
            await context.bot.send_message(
                admin_id,
                f"Запрос на регистрацию:\nФИО: {full_name}\nID: {chat_id}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        await update.message.reply_text("Ваш запрос отправлен на проверку администраторам.")


# Обработка ответа администратора
async def handle_registration_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    data = query.data
    parts = data.split("_")  # Разделяем данные callback_data

    if len(parts) != 2:  # Проверяем, что данных ровно два
        await query.edit_message_text("Ошибка: некорректный формат данных.")
        return

    action, user_id = parts  # Распаковываем только после проверки

    if action == "prinyat":
        if user_id in users:
            users[user_id]["approved"] = True
            save_data()
            await context.bot.send_message(user_id, "Ваша регистрация подтверждена!")
            await query.edit_message_text("Регистрация подтверждена.")
        else:
            await query.edit_message_text("Пользователь не найден.")
    elif action == "decline":
        if user_id in users:
            del users[user_id]
            save_data()
            await context.bot.send_message(user_id, "Ваша регистрация отклонена.")
            await query.edit_message_text("Регистрация отклонена.")
        else:
            await query.edit_message_text("Пользователь не найден.")
    else:
        await query.edit_message_text("Неизвестное действие.")


async def admin_confirm_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Получаем список неподтвержденных пользователей
    unapproved_users = [user_id for user_id, data in users.items() if not data.get("approved")]

    if not unapproved_users:
        await query.edit_message_text("Нет неподтвержденных пользователей.")
        return

    # Формируем кнопки для подтверждения/отклонения
    keyboard = [
        [
            InlineKeyboardButton(f"Подтвердить {users[user_id]['full_name']}", callback_data=f"prinyat_{user_id}"),
            InlineKeyboardButton(f"Отклонить {users[user_id]['full_name']}", callback_data=f"decline_{user_id}")
        ]
        for user_id in unapproved_users
    ]

    await query.edit_message_text(
        "Неподтвержденные пользователи:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    if not users:
        await update.message.reply_text("Список пользователей пуст.")
        return

    # Отображаем только неподтвержденных
    pending = {id: data for id, data in users.items() if not data.get("approved")}

    if not pending:
        await update.message.reply_text("Нет неподтвержденных пользователей.")
        return

    for user_id, data in pending.items():
        keyboard = [
            [
                InlineKeyboardButton("Подтвердить", callback_data=f"prinyat_{user_id}"),
                InlineKeyboardButton("Отклонить", callback_data=f"decline_{user_id}"),
            ]
        ]
        await update.message.reply_text(
            f"Пользователь: {data['full_name']}\nID: {user_id}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# Команда для отображения списка всех пользователей
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    print(user_id)
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    # Загружаем пользователей из файла
    users = load_user_data()

    if not users:
        await update.message.reply_text("Нет зарегистрированных пользователей.")
        return

    # Создаем строку с информацией о пользователях
    user_list_text = "Список всех пользователей:\n\n"
    for user_id, user_data in users.items():
        user_list_text += f"ID: {user_data['id']}\n"
        user_list_text += f"Имя: {user_data['full_name']}\n"
        user_list_text += f"Баланс: {user_data['balance']}\n"
        user_list_text += f"Выполнены задания: {', '.join(user_data['completed_tasks'])}\n"
        user_list_text += f"Подтвержден: {'Да' if user_data['approved'] else 'Нет'}\n"
        user_list_text += f"Заблокирован: {'Да' if user_data['blocked'] else 'Нет'}\n"
        user_list_text += f"Куплено: {', '.join(user_data['purchased'])}\n"
        user_list_text += "-" * 40 + "\n"

    # Отправляем информацию о пользователях
    await update.message.reply_text(user_list_text)


async def approve_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    pending = {id: data for id, data in users.items() if not data.get("approved")}

    if not pending:
        await update.message.reply_text("Нет неподтвержденных пользователей.")
        return

    for pending_user_id, data in pending.items():
        # Обновляем статус пользователя
        users[pending_user_id]["approved"] = True
        try:
            # Отправляем сообщение пользователю
            await context.bot.send_message(
                chat_id=pending_user_id,
                text="Ваша регистрация подтверждена!"
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {pending_user_id}: {e}")

    save_data()

    await update.message.reply_text("Все пользователи подтверждены и уведомлены!")


async def reject_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    pending = {id: data for id, data in users.items() if not data.get("approved")}

    if not pending:
        await update.message.reply_text("Нет неподтвержденных пользователей.")
        return

    for pending_user_id in list(pending.keys()):
        try:
            # Отправляем сообщение пользователю
            await context.bot.send_message(
                chat_id=pending_user_id,
                text="Ваша регистрация отклонена."
            )
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {pending_user_id}: {e}")

        # Удаляем пользователя из списка
        del users[pending_user_id]

    save_data()

    await update.message.reply_text("Все неподтвержденные пользователи отклонены и уведомлены!")


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    try:
        target_user_id = str(context.args[0])  # Получаем ID пользователя из команды, приводим к строке
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите корректный ID пользователя. Пример: /block_user 123456")
        return

    # Загружаем данные пользователей из файла
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except Exception as e:
        await update.message.reply_text("Ошибка загрузки данных пользователей.")
        print(f"Ошибка чтения файла users.json: {e}")
        return

    # Проверяем, существует ли пользователь
    if target_user_id not in users:
        await update.message.reply_text(f"Пользователь с ID {target_user_id} не найден.")
        return

    # Обновляем статус блокировки
    users[target_user_id]["blocked"] = True

    # Сохраняем изменения в файл
    try:
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        await update.message.reply_text("Ошибка сохранения данных пользователей.")
        print(f"Ошибка записи файла users.json: {e}")
        return

    # Уведомляем пользователя о блокировке
    try:
        await context.bot.send_message(
            chat_id=int(target_user_id),
            text="Вы были заблокированы администратором. Вы больше не можете взаимодействовать с ботом."
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения пользователю {target_user_id}: {e}")

    await update.message.reply_text(f"Пользователь с ID {target_user_id} заблокирован.")


async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    try:
        target_user_id = str(context.args[0])  # Получаем ID пользователя из команды, приводим к строке
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите корректный ID пользователя. Пример: /unblock_user 123456")
        return

    # Загружаем данные пользователей из файла
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            users = json.load(f)
    except Exception as e:
        await update.message.reply_text("Ошибка загрузки данных пользователей.")
        print(f"Ошибка чтения файла users.json: {e}")
        return

    # Проверяем, существует ли пользователь
    if target_user_id not in users:
        await update.message.reply_text(f"Пользователь с ID {target_user_id} не найден.")
        return

    # Проверяем, заблокирован ли пользователь
    if not users[target_user_id].get("blocked", False):
        await update.message.reply_text(f"Пользователь с ID {target_user_id} не заблокирован.")
        return

    # Снимаем блокировку
    users[target_user_id]["blocked"] = False

    # Сохраняем изменения в файл
    try:
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        await update.message.reply_text("Ошибка сохранения данных пользователей.")
        print(f"Ошибка записи файла users.json: {e}")
        return

    # Уведомляем пользователя о разблокировке
    try:
        await context.bot.send_message(
            chat_id=int(target_user_id),
            text="Вы были разблокированы администратором. Теперь вы можете снова взаимодействовать с ботом."
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения пользователю {target_user_id}: {e}")

    await update.message.reply_text(f"Пользователь с ID {target_user_id} разблокирован.")


async def set_bot_commands(application):
    # Команды для всех пользователей
    user_commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("help", "Помощь по боту"),
    ]
    await application.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Устанавливаем команды только для зарегистрированных и подтвержденных пользователей
    for user_id in users:
        user = users[user_id]
        if user.get("approved"):
            user_commands += [
                BotCommand("help", "Помощь по боту"),
                BotCommand("wallet", "Ваш баланс"),
                BotCommand("market", "Магазин товаров"),
                BotCommand("tasks", "Список заданий"),
                BotCommand("purchased", "Купленные товары"),
            ]
            await application.bot.set_my_commands(user_commands, scope=BotCommandScopeChat(user_id))

    # Устанавливаем команды только для администраторов в личных чатах
    admin_commands = [
        BotCommand("help", "Команды пользователей"),
        BotCommand("admin", "Панель администратора"),
        BotCommand("addadmin", "Добавить администратора"),
        BotCommand("removeadmin", "Удалить администратора"),
        BotCommand("pending_users", "Неподтвержденные пользователи"),
        BotCommand("approve_all", "Подтвердить регистрацию всех пользователей"),
        BotCommand("reject_all", "Отклонить регистрацию всех пользователей"),
        BotCommand("users_list", "Список всех пользователей"),
        BotCommand("block_user", "Заблокировать пользователя"),
        BotCommand("unblock_user", "Разблокировать пользователя"),
        # BotCommand("add_item", "Добавить товар"),
        # BotCommand("edit_item", "Изменить товар"),
        # BotCommand("delete_item", "Удалить товар"),
        # BotCommand("cancel", "Отменить добавление или изменение товара")
    ]
    for admin_id in admins:
        await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(admin_id))


async def clear_commands(application):
    # Удаляем все команды для всех областей
    await application.bot.set_my_commands([])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("Подтвердить регистрацию", callback_data="admin_confirm_users")],
            [InlineKeyboardButton("Управление заданиями", callback_data="admin_tasks")],
            [InlineKeyboardButton("Проверка заданий", callback_data="admin_check_tasks")]
        ]
        await update.message.reply_text(
            "Добро пожаловать в панель администратора. Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("У вас нет прав администратора.")


async def check_pending_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    load_data()

    # Ищем все задания со статусом "pending"
    pending_tasks = []
    for user_id, tasks_list in submissions.items():
        for task in tasks_list:
            if task["status"] == "pending":
                user = users.get(user_id)
                task_info = tasks.get(str(task["task_id"]))
                if user and task_info:
                    task_data = {
                        "user_full_name": user["full_name"],
                        "task_title": task_info["title"],
                        "task_description": task_info["description"],
                        "task_text": task["text"] if task["text"] else "Нет текста",
                        "task_photo": task["photo_path"] if task["photo_path"] else "Нет фото",
                        "task_id": task["task_id"],
                        "user_id": user_id
                    }
                    pending_tasks.append(task_data)

    if not pending_tasks:
        await query.edit_message_text("Нет заданий на проверку.")
        return

    # Отправляем карточки с заданиями
    for task in pending_tasks:
        keyboard = [
            [InlineKeyboardButton("Принять", callback_data=f"accept_{task['task_id']}"),
             InlineKeyboardButton("Отклонить", callback_data=f"reject_{task['task_id']}")]
        ]

        task_card = (
            f"Задание: {task['task_title']}\n"
            f"Отправлено пользователем: {task['user_full_name']}\n"
            f"Описание: {task['task_description']}\n"
            f"Текст задания: {task['task_text']}\n"
            f"Фото: {task['task_photo'] if task['task_photo'] != 'Нет фото' else 'Нет'}"
        )

        # Если есть фото, отправляем его
        if task['task_photo'] != "Нет фото":
            image_path = os.path.join(os.getcwd(), task['task_photo'])
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=task_card,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{task_card}\n⚠️ Фото не найдено по указанному пути.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            # Если фото нет, отправляем только текст
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=task_card,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )


# Загрузочные функции (пример):
def load_users():
    # Здесь должна быть функция загрузки данных из users.json
    with open('users.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def load_tasks():
    # Здесь должна быть функция загрузки данных из tasks.json
    with open('tasks.json', 'r', encoding='utf-8') as f:
        return json.load(f)


async def handle_task_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    data = query.data
    action, task_id = data.split("_")  # Разделяем данные (accept или reject и task_id)

    # Идентификатор администратора, который нажал на кнопку
    admin_id = str(update.effective_chat.id)

    # Найдем пользователя и задание
    task = None
    user_id = None

    # Логгирование данных для диагностики
    print(f"Администратор {admin_id} обрабатывает действие {action} для задания {task_id}")

    for uid, tasks_list in submissions.items():
        for t in tasks_list:
            if t["task_id"] == task_id and t["status"] == "pending":
                task = t
                user_id = uid
                break
        if task:
            break

    # Если задание не найдено
    if task is None:
        await query.message.reply_text("Задание не найдено или уже обработано.")
        return

    # Загружаем данные пользователя
    user = users.get(user_id)
    if not user:
        await query.message.reply_text("Пользователь не найден.")
        return

    # Логгирование для проверки данных пользователя
    print(f"Обрабатывается пользователь с ID {user_id}: {user}")

    if action == "accept":
        task["status"] = "accepted"
        task["admin_comment"] = "Задание принято."

        # Добавляем задание в completed_tasks и обновляем баланс
        if task_id not in user["completed_tasks"]:
            user["completed_tasks"].append(task_id)

            # Загружаем информацию о задании для получения награды
            task_info = tasks.get(task_id, {})
            points = task_info.get("reward", 0)  # По умолчанию 0 баллов
            user["balance"] += points

            # Уведомляем пользователя о принятии задания
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"Ваше задание '{task_info.get('title', 'Задание')}' принято. Вам начислено {points} баллов!"
                )
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    elif action == "reject":
        task["status"] = "rejected"
        task["admin_comment"] = "Задание отклонено."

        # Уведомляем пользователя об отклонении задания
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"Ваше задание '{task_id}' отклонено. Комментарий администратора: {task['admin_comment']}"
            )
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    # Сохраняем обновленные данные
    save_json("submissions.json", submissions)
    save_json("users.json", users)

    # Обновляем сообщение администратора
    try:
        await query.edit_message_text(
            f"Задание {task_id} {'принято' if action == 'accept' else 'отклонено'}."
        )
    except Exception as e:
        print(f"Ошибка редактирования сообщения администратора: {e}")


async def notify_user_of_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE, task_id: str, status: str):
    chat_id = str(update.effective_chat.id)
    if status == "accepted":
        message = "Ваше задание было принято!"
    else:
        message = "Ваше задание было отклонено."

    await context.bot.send_message(chat_id, message)


async def admin_manage_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Добавить задание", callback_data="add_task")],
        [InlineKeyboardButton("Редактировать задание", callback_data="edit_task")],
        [InlineKeyboardButton("Удалить задание", callback_data="delete_task")]
    ]
    await update.callback_query.message.edit_text(
        "Выберите действие с заданиями:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Введите данные нового задания в формате:\nНазвание|Описание|Награда|Тип (text/photo/both)")
    context.user_data['task_action'] = "add_task"


async def add_task_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.message.text.split("|")
        if len(data) != 4:
            await update.message.reply_text(
                "Неверный формат данных. Используйте формат:\nНазвание|Описание|Награда|Тип (text/photo/both)"
            )
            return  # Возвращаемся, чтобы снова ждать правильный ввод

        title, description, reward, task_type = data

        # Проверяем, что награда - это число
        try:
            reward = int(reward.strip())
        except ValueError:
            await update.message.reply_text(
                "Неверный формат награды. Награда должна быть числом. Пожалуйста, попробуйте снова."
            )
            return  # Возвращаемся, чтобы снова ждать правильный ввод

        # Проверяем корректность типа задания
        if task_type.strip() not in ["text", "photo", "both"]:
            await update.message.reply_text(
                "Неверный тип задания. Доступные типы: text, photo, both"
            )
            return  # Возвращаемся, чтобы снова ждать правильный ввод

        # Генерируем новый ID задания
        task_id = str(max(map(int, tasks.keys()), default=0) + 1)
        tasks[task_id] = {
            "title": title.strip(),
            "description": description.strip(),
            "reward": reward,
            "requires": task_type.strip()
        }

        # Сохраняем данные
        save_data()

        await update.message.reply_text(
            f"Новое задание добавлено:\nНазвание: {title}\nОписание: {description}\nНаграда: {reward} баллов\nТип задания: {task_type}."
        )

        # Завершаем текущее действие, чтобы избежать зацикливания
        context.user_data.pop('task_action', None)

    except Exception as e:
        # Обрабатываем исключение и уведомляем об ошибке
        await update.message.reply_text(f"Ошибка добавления задания: {e}")

    finally:
        # В любом случае сбрасываем состояние, чтобы избежать повторного выполнения
        context.user_data['task_action'] = None


async def edit_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_list = "Выберите задание для редактирования (укажите ID):\n"
    for task_id, task in tasks.items():
        task_list += f"ID: {task_id} | {task['title']} | Тип: {task['requires']}\n"
    await update.callback_query.message.reply_text(task_list)
    context.user_data['task_action'] = "edit_task"
    context.user_data['editing_task_id'] = None  # Очистка ID задания
    context.user_data['editing_step'] = 'title'  # Начинаем с названия


async def edit_task_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что у нас есть ID задания для редактирования
    task_id = context.user_data.get('editing_task_id')

    if task_id is None:
        # Если ID задания еще не установлен, это означает, что администратор только что начал редактирование.
        task_id = update.message.text.strip()
        task = tasks.get(task_id)

        if not task:
            await update.message.reply_text("Задание с таким ID не найдено. Попробуйте снова.")
            return  # Возвращаемся, чтобы снова ожидать корректный ввод ID задания

        # Сохраняем ID задания в контекст пользователя
        context.user_data['editing_task_id'] = task_id
        context.user_data['editing_step'] = 'title'  # Начинаем редактирование с названия задания
        await update.message.reply_text(f"Вы выбрали задание: {task['title']}\nТеперь введите новое название задания (если не хотите изменять, просто отправьте текущее).")
        return

    # Получаем задание из списка заданий
    task = tasks.get(task_id)
    if not task:
        await update.message.reply_text("Произошла ошибка, задание не найдено. Завершаем редактирование.")
        context.user_data.pop('editing_task_id', None)
        context.user_data.pop('editing_step', None)
        return

    # Проверяем текущий шаг редактирования
    editing_step = context.user_data.get('editing_step')

    if editing_step == 'title':
        # Редактируем название задания
        new_title = update.message.text.strip()
        task['title'] = new_title
        context.user_data['editing_step'] = 'description'  # Переходим к следующему шагу редактирования
        await update.message.reply_text(f"Название изменено на: {task['title']}\nТеперь введите описание задания.")
        return

    elif editing_step == 'description':
        # Редактируем описание задания
        new_description = update.message.text.strip()
        task['description'] = new_description
        context.user_data['editing_step'] = 'reward'  # Переходим к следующему шагу редактирования
        await update.message.reply_text(f"Описание изменено на: {task['description']}\nТеперь введите награду задания (число).")
        return

    elif editing_step == 'reward':
        # Редактируем награду задания
        try:
            new_reward = int(update.message.text.strip())
            task['reward'] = new_reward
            context.user_data['editing_step'] = 'requires'  # Переходим к следующему шагу редактирования
            await update.message.reply_text(f"Награда изменена на: {task['reward']} баллов\nТеперь введите тип задания (text/photo/both).")
        except ValueError:
            await update.message.reply_text("Неверный формат награды. Награда должна быть числом. Попробуйте снова.")
        return

    elif editing_step == 'requires':
        # Редактируем тип задания
        task_type = update.message.text.strip().lower()
        if task_type in ["text", "photo", "both"]:
            task['requires'] = task_type
            save_data()  # Сохраняем изменения в задания
            await update.message.reply_text(f"Тип задания изменен на: {task['requires']}\nЗадание успешно обновлено.")
            # Завершаем процесс редактирования, удаляя временные данные
            context.user_data.pop('editing_task_id', None)
            context.user_data.pop('editing_step', None)
        else:
            await update.message.reply_text("Неверный тип задания. Используйте один из вариантов: text, photo, both.")
        return

    else:
        # Если произошло что-то непредвиденное, сбрасываем состояние
        await update.message.reply_text("Произошла ошибка при редактировании. Завершаем процесс редактирования.")
        context.user_data.pop('editing_task_id', None)
        context.user_data.pop('editing_step', None)


async def delete_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_list = "Выберите задание для удаления (укажите ID):\n"
    for task_id, task in tasks.items():
        task_list += f"ID: {task_id} | {task['title']} | Тип: {task['requires']}\n"
    await update.callback_query.message.reply_text(task_list)
    context.user_data['task_action'] = "delete_task"


async def delete_task_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        task_id = update.message.text.strip()

        # Проверяем, существует ли задание с указанным ID
        if task_id not in tasks:
            await update.message.reply_text("Задание с таким ID не найдено. Попробуйте снова.")
            return  # Возвращаемся, чтобы снова ожидать корректный ввод

        # Удаляем задание
        del tasks[task_id]
        save_data()  # Сохраняем изменения

        await update.message.reply_text(f"Задание с ID {task_id} успешно удалено.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка удаления задания: {e}")

    finally:
        # В любом случае сбрасываем состояние редактирования, чтобы избежать повторного выполнения
        context.user_data.pop('task_action', None)


# Вспомогательные функции для рынка
async def show_market_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item=None):
    chat_id = str(update.effective_chat.id)
    user = users.get(chat_id)
    if not user:
        await update.message.reply_text("Вы не зарегистрированы!")
        return

    # Загружаем актуальные данные о товарах
    market = load_market_data()

    # Если item не передан, используем текущий индекс из context.user_data
    if item is None:
        index = context.user_data.get('market_index', 0)
        item = market[index]

    # Создаем клавиатуру с одной кнопкой "Купить"
    keyboard = [[InlineKeyboardButton("Купить", callback_data="buy_item")]]

    # Определяем путь к изображению
    image_path = os.path.join(os.getcwd(), item['image'])
    if os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            # Проверяем, является ли вызов ответом на кнопку или новым сообщением
            if hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_photo(
                    photo=photo,
                    caption=(
                        f"Название: {item['name']}\n"
                        f"Ваши баллы: {user['balance']}\n"
                        f"Цена: {item['price']}\n"
                        f"В наличии: ???"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_photo(
                    photo=photo,
                    caption=(
                        f"Название: {item['name']}\n"
                        f"Ваши баллы: {user['balance']}\n"
                        f"Цена: {item['price']}\n"
                        f"В наличии: ???"
                    ),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
    else:
        await update.message.reply_text(f"Изображение для товара {item['name']} не найдено.")


async def handle_market_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Уведомляем Telegram, что кнопка нажата
    chat_id = str(query.message.chat_id)
    user = users.get(chat_id)

    if not user:
        await query.message.reply_text("Вы не зарегистрированы!")
        return
    elif not user.get("approved"):
        await query.message.reply_text("Ваша регистрация не подтверждена администраторами!")
        return

    data = query.data
    index = context.user_data.get('market_index', 0)

    if data == "prev_item":
        # Переход к предыдущему товару
        index = (index - 1) % len(market)  # Циклический переход
        context.user_data['market_index'] = index
        await show_market_item(update, context)

    elif data == "next_item":
        # Переход к следующему товару
        index = (index + 1) % len(market)  # Циклический переход
        context.user_data['market_index'] = index
        await show_market_item(update, context)

    elif data == "show_all_items":
        # Показать карточки всех товаров
        for item in market:
            await show_market_item(update, context, item=item)
            await asyncio.sleep(0.5)  # Задержка для предотвращения ограничения Telegram

    elif data == "buy_item":
        # Покупка текущего товара
        item = market[index]
        if item['quantity'] <= 0:
            await query.message.reply_text(f"Товара {item['name']} больше нет в наличии!")
        elif user['balance'] < item['price']:
            await query.message.reply_text(f"У вас недостаточно баллов для покупки {item['name']}!")
        else:
            # Списываем баллы и уменьшаем количество товара
            user['balance'] -= item['price']
            item['quantity'] -= 1
            user['purchased'].append(item['name'])
            save_data()
            await query.message.reply_text(
                f"Вы успешно купили {item['name']} за {item['price']} баллов!\n"
                f"Ваш баланс: {user['balance']} баллов."
            )
        await show_market_item(update, context)


async def start_add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    context.user_data['add_item'] = {}
    await update.message.reply_text(
        "Введите данные товара в формате:\n"
        "<название>, <цена>, <количество>\n"
        "Пример: Приз 3, 200, 10"
    )
    return "WAITING_FOR_ITEM_DETAILS"


async def add_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        details = update.message.text.split(",")
        name, price, quantity = details[0].strip(), int(details[1].strip()), int(details[2].strip())
        context.user_data['add_item'] = {"name": name, "price": price, "quantity": quantity}
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Неверный формат. Пожалуйста, отправьте данные товара в формате:\n"
            "<название>, <цена>, <количество>"
        )
        return "WAITING_FOR_ITEM_DETAILS"

    await update.message.reply_text("Теперь отправьте изображение для товара.")
    return "WAITING_FOR_ITEM_IMAGE"


async def add_item_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, отправьте изображение товара.")
        return "WAITING_FOR_ITEM_IMAGE"

    photo = update.message.photo[-1]
    file = await photo.get_file()

    file_path = f"images/{context.user_data['add_item']['name'].replace(' ', '_')}.jpg"
    await file.download_to_drive(file_path)

    context.user_data['add_item']['image'] = file_path
    market.append(context.user_data['add_item'])
    save_data()

    await update.message.reply_text(f"Товар '{context.user_data['add_item']['name']}' успешно добавлен!")
    context.user_data.pop('add_item', None)
    return ConversationHandler.END


async def start_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    await update.message.reply_text("Введите название товара, который хотите изменить:")
    return "WAITING_FOR_ITEM_NAME"


async def edit_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item_name = update.message.text.strip()
    item = next((i for i in market if i["name"] == item_name), None)

    if not item:
        await update.message.reply_text("Товар не найден. Попробуйте снова.")
        return "WAITING_FOR_ITEM_NAME"

    context.user_data['edit_item'] = item
    await update.message.reply_text(
        f"Текущие данные:\nНазвание: {item['name']}\nЦена: {item['price']}\nКоличество: {item['quantity']}\n"
        "Введите новые данные в формате:\n<цена>, <количество>"
    )
    return "WAITING_FOR_NEW_DETAILS"


async def update_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        details = update.message.text.split(",")
        new_price, new_quantity = int(details[0].strip()), int(details[1].strip())

        context.user_data['edit_item']['price'] = new_price
        context.user_data['edit_item']['quantity'] = new_quantity
        save_data()

        await update.message.reply_text("Данные товара успешно обновлены!")
        return ConversationHandler.END
    except (IndexError, ValueError):
        await update.message.reply_text("Неверный формат. Попробуйте снова.")
        return "WAITING_FOR_NEW_DETAILS"


# Функция для загрузки данных о товарах
def load_market_data():
    try:
        with open('market.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []  # Возвращаем пустой список, если файл не найден


# Функция для сохранения данных о товарах
def save_market_data(market):
    with open('market.json', 'w', encoding='utf-8') as file:
        json.dump(market, file, ensure_ascii=False, indent=4)


async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    # Получаем название товара, введенное пользователем
    try:
        item_name = " ".join(context.args)  # Объединяем все аргументы в одну строку
    except IndexError:
        await update.message.reply_text("Пожалуйста, укажите название товара для удаления.")
        return

    # Логирование для диагностики
    print(f"Ищем товар с названием: '{item_name}'")

    # Загружаем данные о товарах
    market = load_market_data()

    # Ищем товар с указанным названием
    item_to_delete = None
    for item in market:
        print(f"Проверяем товар: {item['name']}")
        if item['name'] == item_name:  # Сравниваем по точному совпадению
            item_to_delete = item
            break

    if not item_to_delete:
        await update.message.reply_text(f"Товар с названием '{item_name}' не найден.")
        return

    # Удаляем товар из списка
    market.remove(item_to_delete)

    # Сохраняем изменения
    save_market_data(market)

    # Обновляем список товаров
    await update.message.reply_text(f"Товар '{item_name}' успешно удален.")


async def cancel_add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет процесс добавления товара."""
    await update.message.reply_text("Добавление товара отменено.")
    return ConversationHandler.END


async def cancel_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет процесс редактирования товара."""
    await update.message.reply_text("Редактирование товара отменено.")
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Логгирование исключений
    print(f"❌ Произошла ошибка: {context.error}")
    import traceback
    traceback.print_exc()
    
    # Если есть update, логируем информацию о нем
    if update:
        print(f"   Update: {update}")


# Новая универсальная функция для обработки текстовых сообщений
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_action = context.user_data.get('task_action')

    if task_action == "perform_task":
        task_id = context.user_data.get('current_task')
        if not task_id:
            await update.message.reply_text("Вы не выбрали задание для выполнения.")
            return

        task = tasks.get(str(task_id))
        requires = task.get("requires", "both")

        # Если задание требует текста и фото
        if requires == "both":
            if update.message.photo and update.message.caption:
                # Если пришли и фото, и caption (текст), обрабатываем это
                await handle_both_submission(update, context)
            else:
                await update.message.reply_text(
                    "Это задание требует фото и текст в виде caption. Пожалуйста, отправьте оба элемента.")

        # Обработка других типов задания, например, только текст или только фото
        elif requires == "text" and update.message.text:
            await save_text_submission(update, context)
        elif requires == "photo" and update.message.photo:
            await save_photo_submission(update, context)
        else:
            await update.message.reply_text(
                f"Это задание требует {requires}. Пожалуйста, отправьте необходимые элементы.")

    # Обработка других действий
    elif task_action == "add_task":
        await add_task_finish(update, context)
    elif task_action == "edit_task":
        await edit_task_finish(update, context)
    elif task_action == "delete_task":
        await delete_task_finish(update, context)
    else:
        await register_user(update, context)


# Функция для обработки отправки текста
async def save_text_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.get('current_task')
    user_id = str(update.effective_chat.id)
    text = update.message.text

    # Загружаем существующие задания
    submissions = load_json("submissions.json")
    if user_id not in submissions:
        submissions[user_id] = []

    # Ищем существующую запись задания
    task_found = False
    for task in submissions[user_id]:
        if task["task_id"] == task_id:
            task["text"] = text
            task["photo_path"] = None  # Обновляем, если только текст
            task["status"] = "pending"
            task["admin_comment"] = None
            task_found = True
            break

    # Если запись не найдена, добавляем новое задание
    if not task_found:
        submissions[user_id].append({
            "task_id": task_id,
            "photo_path": None,  # Нет фото
            "text": text,
            "status": "pending",
            "admin_comment": None
        })

    # Сохраняем обновления
    save_json("submissions.json", submissions)

    await update.message.reply_text("Ваш текст отправлен на проверку.")

    # Оповещение администраторов
    for admin_id in admins:
        await context.bot.send_message(
            chat_id=admin_id,
            text="Пришло новое задание на проверку."
        )


async def save_photo_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.get('current_task')
    user_id = str(update.effective_chat.id)

    # Сохраняем фото
    photo = update.message.photo[-1]
    file = await photo.get_file()
    save_path = os.path.join("uploads", f"user_{user_id}_task_{task_id}.jpg")
    await file.download_to_drive(save_path)

    # Загружаем существующие задания
    submissions = load_json("submissions.json")
    if user_id not in submissions:
        submissions[user_id] = []

    # Ищем существующую запись задания
    task_found = False
    for task in submissions[user_id]:
        if task["task_id"] == task_id:
            task["photo_path"] = save_path
            task["text"] = None  # Обновляем, если только фото
            task["status"] = "pending"
            task["admin_comment"] = None
            task_found = True
            break

    # Если запись не найдена, добавляем новое задание
    if not task_found:
        submissions[user_id].append({
            "task_id": task_id,
            "photo_path": save_path,
            "text": None,
            "status": "pending",
            "admin_comment": None
        })

    # Сохраняем обновления
    save_json("submissions.json", submissions)

    await update.message.reply_text("Ваше фото отправлено на проверку.")

    # Оповещение администраторов
    for admin_id in admins:
        await context.bot.send_message(
            chat_id=admin_id,
            text="Пришло новое задание на проверку."
        )


async def handle_both_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data.get('current_task')
    user_id = str(update.effective_chat.id)

    # Сохраняем фото
    photo = update.message.photo[-1]
    file = await photo.get_file()
    save_path = os.path.join("uploads", f"user_{user_id}_task_{task_id}.jpg")
    await file.download_to_drive(save_path)

    # Сохраняем текст из caption
    text = update.message.caption

    # Загружаем существующие задания
    submissions = load_json("submissions.json")
    if user_id not in submissions:
        submissions[user_id] = []

    # Ищем существующую запись задания
    task_found = False
    for task in submissions[user_id]:
        if task["task_id"] == task_id:
            task["photo_path"] = save_path
            task["text"] = text
            task["status"] = "pending"
            task["admin_comment"] = None
            task_found = True
            break

    # Если запись не найдена, добавляем новое задание
    if not task_found:
        submissions[user_id].append({
            "task_id": task_id,
            "photo_path": save_path,
            "text": text,
            "status": "pending",
            "admin_comment": None
        })

    # Сохраняем обновления
    save_json("submissions.json", submissions)

    await update.message.reply_text("Ваше выполнение задания (текст и фото) отправлено на проверку.")

    # Оповещение администраторов
    for admin_id in admins:
        await context.bot.send_message(
            chat_id=admin_id,
            text="Пришло новое задание на проверку."
        )


# Главная точка входа
def main():
    print("=" * 50)
    print("Запуск Telegram бота...")
    print("=" * 50)
    
    try:
        load_data()  # Загрузка данных пользователей, магазина и заданий
        print("✓ Данные загружены успешно")
    except Exception as e:
        print(f"⚠ Ошибка загрузки данных: {e}")
    
    try:
        load_admins()  # Загрузка списка администраторов
        print(f"✓ Администраторы загружены: {len(admins)} админов")
    except Exception as e:
        print(f"⚠ Ошибка загрузки администраторов: {e}")

    # Создаем цикл событий вручную
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Получаем токен из переменной окружения
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ ОШИБКА: BOT_TOKEN environment variable is not set!")
        print("   Установите переменную окружения BOT_TOKEN перед запуском бота.")
        raise ValueError("BOT_TOKEN environment variable is not set. Please set it before running the bot.")
    
    print(f"✓ Токен бота получен (длина: {len(bot_token)} символов)")
    
    try:
        app = Application.builder().token(bot_token).build()
        print("✓ Приложение Telegram создано успешно")
    except Exception as e:
        print(f"❌ Ошибка создания приложения: {e}")
        raise

    try:
        # Очищаем панель команд перед запуском
        loop.run_until_complete(clear_commands(app))
        print("✓ Команды очищены")
    except Exception as e:
        print(f"⚠ Ошибка очистки команд: {e}")

    try:
        # Устанавливаем команды перед запуском
        loop.run_until_complete(set_bot_commands(app))
        print("✓ Команды установлены")
    except Exception as e:
        print(f"⚠ Ошибка установки команд: {e}")

    # Пользовательские команды
    app.add_handler(CommandHandler("start", lambda u, c: command_wrapper(u, c, start)))
    app.add_handler(CommandHandler("help", lambda u, c: command_wrapper(u, c, help_command)))
    app.add_handler(CommandHandler("tasks", lambda u, c: command_wrapper(u, c, tasks_command)))
    app.add_handler(CommandHandler("wallet", lambda u, c: command_wrapper(u, c, wallet_command)))
    app.add_handler(CommandHandler("market", lambda u, c: command_wrapper(u, c, market_command)))
    app.add_handler(CommandHandler("purchased", lambda u, c: command_wrapper(u, c, purchased_command)))
    for task_id in tasks.keys():
        app.add_handler(CommandHandler(f"task_{task_id}", task_command_handler(task_id)))

    # Административные команды
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("pending_users", pending_users))
    app.add_handler(CommandHandler("approve_all", approve_all_users))
    app.add_handler(CommandHandler("reject_all", reject_all_users))
    app.add_handler(CommandHandler("block_user", block_user))
    app.add_handler(CommandHandler("unblock_user", unblock_user))
    app.add_handler(CommandHandler("users_list", list_users))

    add_item_handler = ConversationHandler(
        entry_points=[CommandHandler("add_item", start_add_item)],
        states={
            "WAITING_FOR_ITEM_DETAILS": [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_details)],
            "WAITING_FOR_ITEM_IMAGE": [MessageHandler(filters.PHOTO, add_item_image)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_item)],
    )

    edit_item_handler = ConversationHandler(
        entry_points=[CommandHandler("edit_item", start_edit_item)],
        states={
            "WAITING_FOR_ITEM_NAME": [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_item_details)],
            "WAITING_FOR_NEW_DETAILS": [MessageHandler(filters.TEXT & ~filters.COMMAND, update_item_details)],
        },
        fallbacks=[CommandHandler("cancel", cancel_edit_item)],
    )

    app.add_handler(add_item_handler)
    app.add_handler(edit_item_handler)
    app.add_handler(CommandHandler("delete_item", delete_item))

    app.add_handler(CallbackQueryHandler(admin_manage_tasks, pattern="admin_tasks"))
    app.add_handler(CallbackQueryHandler(add_task_start, pattern="add_task"))
    app.add_handler(CallbackQueryHandler(edit_task_start, pattern="edit_task"))
    app.add_handler(CallbackQueryHandler(delete_task_start, pattern="delete_task"))
    app.add_handler(CallbackQueryHandler(admin_confirm_users, pattern="admin_confirm_users"))

    app.add_handler(CallbackQueryHandler(check_pending_tasks, pattern="admin_check_tasks"))

    app.add_handler(CallbackQueryHandler(handle_registration_response, pattern=r"^(prinyat|decline)_\d+$"))

    app.add_handler(CallbackQueryHandler(handle_task_response, pattern=r"^(accept|reject)_\d+$"))

    app.add_handler(CallbackQueryHandler(handle_market_button))

    # Для обработки текста после команды
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO & ~filters.COMMAND, handle_text_input))

    app.add_error_handler(error_handler)

    print("=" * 50)
    print("Бот запущен и готов к работе!")
    print("Ожидание сообщений...")
    print("=" * 50)
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\n✓ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка при работе бота: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()