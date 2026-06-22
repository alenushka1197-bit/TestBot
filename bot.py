import telebot
from telebot.types import Message
import time
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# ===== НАСТРОЙКИ ИЗ .env =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "480145722"))  # преобразуем в число

# Проверка: если токен не загрузился
if not TOKEN or not ADMIN_ID:
    raise ValueError(
        "❌ Ошибка: не удалось загрузить BOT_TOKEN или ADMIN_ID из .env файла!"
    )

# ===============================

bot = telebot.TeleBot(TOKEN)

# Список вопросов анкеты
QUESTIONS = [
    "Как вас зовут?",
    "Сколько вам лет?",
    "Где вы живете? (город, страна)",
    "Чем вы занимаетесь? (работа/учеба)",
    "Ваш номер телефона (для связи)",
    "Дополнительный комментарий (по желанию)",
    "новый ворос",
]

# Хранилище временных данных пользователей
user_data = {}


# Команда /start
@bot.message_handler(commands=["start"])
def start_command(message: Message):
    chat_id = message.chat.id
    # Сброс данных пользователя
    user_data[chat_id] = {"answers": [], "question_index": 0}
    bot.send_message(chat_id, "📝 Добро пожаловать! Отвечайте на вопросы анкеты.")
    time.sleep(0.5)
    ask_next_question(chat_id)


# Функция для отправки следующего вопроса
def ask_next_question(chat_id):
    data = user_data.get(chat_id)
    if data is None:
        return

    index = data["question_index"]
    if index < len(QUESTIONS):
        bot.send_message(
            chat_id, f"❓ Вопрос {index+1}/{len(QUESTIONS)}:\n{QUESTIONS[index]}"
        )
    else:
        # Все вопросы заданы — завершаем анкету
        finish_survey(chat_id)


# Обработка текстовых сообщений (ответов на вопросы)
@bot.message_handler(func=lambda msg: True)
def handle_answer(message: Message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Если пользователь не начал анкету — игнорируем
    if chat_id not in user_data:
        bot.send_message(chat_id, "Напишите /start, чтобы начать анкету.")
        return

    data = user_data[chat_id]
    index = data["question_index"]

    # Если ответили пустым сообщением — просим ввести текст
    if not text:
        bot.send_message(chat_id, "Пожалуйста, введите текстовый ответ.")
        return

    # Сохраняем ответ на текущий вопрос
    data["answers"].append(text)

    # Переходим к следующему вопросу
    data["question_index"] += 1

    # Задаём следующий вопрос или завершаем
    ask_next_question(chat_id)


# Завершение опроса
def finish_survey(chat_id):
    data = user_data.get(chat_id)
    if data is None:
        return

    answers = data["answers"]

    # ---- ОТПРАВКА ТОЛЬКО АДМИНИСТРАТОРУ (ПОЛЬЗОВАТЕЛЬ НИЧЕГО НЕ ВИДИТ) ----
    final_report = "✅ <b>НОВАЯ АНКЕТА ЗАПОЛНЕНА</b>\n\n"
    
    # 👇 ДОБАВЛЕНА ССЫЛКА НА ПОЛЬЗОВАТЕЛЯ ЧЕРЕЗ @
    # Получаем информацию о пользователе
    try:
        user_info = bot.get_chat(chat_id)
        username = user_info.username if user_info.username else None
        
        if username:
            final_report += f"👤 Пользователь: <a href='https://t.me/{username}'>@{username}</a>\n"
        else:
            final_report += f"👤 Пользователь: <a href='tg://user?id={chat_id}'>ID: {chat_id}</a>\n"
            
    except Exception as e:
        # Если не удалось получить username, используем ID
        final_report += f"👤 Пользователь: <a href='tg://user?id={chat_id}'>ID: {chat_id}</a>\n"
    
    final_report += f"🕐 Время: {time.strftime('%d.%m.%Y %H:%M:%S')}\n\n"

    for i, q in enumerate(QUESTIONS):
        final_report += f"<b>{i+1}. {q}</b>\n{answers[i]}\n\n"

    try:
        # Отправляем только админу
        bot.send_message(ADMIN_ID, final_report, parse_mode="HTML")

        # Пользователю отправляем только короткое сообщение без ответов
        bot.send_message(chat_id, "✅ Спасибо! Ваши ответы успешно отправлены.")

    except Exception as e:
        print(f"Ошибка отправки отчёта: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже.")

    # Удаляем данные пользователя
    del user_data[chat_id]


# Команда /cancel — отмена анкеты
@bot.message_handler(commands=["cancel"])
def cancel_command(message: Message):
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    bot.send_message(chat_id, "❌ Анкета отменена. Для начала новой напишите /start")


# Запуск бота
if __name__ == "__main__":
    print("🤖 Бот запущен...")
    print(f"✅ Токен загружен: {TOKEN[:10]}...")
    print(f"✅ Админ ID: {ADMIN_ID}")
    bot.infinity_polling()
