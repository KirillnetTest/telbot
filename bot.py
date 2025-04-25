import os
import random
import logging
import psycopg2
from telebot import TeleBot, types
from telebot.handler_backends import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Telegram bot token not found in environment variables.")

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

bot = TeleBot(TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    add_russian = State()
    add_english = State()
    delete_word = State()

def check_db_connection():
    """Check database connection and required tables"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'words'
                    ) AND EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'user_words'
                    ) AND EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'results'
                    )
                """)
                return cursor.fetchone()[0]
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        return False

def get_random_word(user_id):
    """Get random word from either default or user words"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT russian, english
                    FROM (
                        (SELECT russian, english FROM words)
                        UNION ALL
                        (SELECT russian, english FROM user_words WHERE user_id = %s)
                    ) AS combined_words
                    ORDER BY RANDOM() LIMIT 1
                """, (user_id,))
                return cursor.fetchone()
    except psycopg2.Error as e:
        logger.error(f"Database error in get_random_word: {e}")
        return None

def get_random_english_words(user_id, exclude_word, limit=3):
    """Get random English words excluding the correct answer"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT english
                    FROM (
                        (SELECT english FROM words WHERE english != %s)
                        UNION ALL
                        (SELECT english FROM user_words WHERE user_id = %s AND english != %s)
                    ) AS combined_words
                    ORDER BY RANDOM() LIMIT %s
                """, (exclude_word, user_id, exclude_word, limit))
                results = [row[0] for row in cursor.fetchall()]
                logger.info(f"get_random_english_words: Fetched {len(results)} words for user_id={user_id}, exclude_word={exclude_word}")
                return results
    except psycopg2.Error as e:
        logger.error(f"Database error in get_random_english_words: {e}")
        return []

def add_user_word(user_id, russian, english):
    """Add a word to user's personal dictionary"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_words (user_id, russian, english)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, russian, english) DO NOTHING
                    RETURNING id
                """, (user_id, russian, english))
                conn.commit()
                return cursor.fetchone() is not None
    except psycopg2.Error as e:
        logger.error(f"Database error in add_user_word: {e}")
        return False

def save_answer_result(user_id, russian_word, user_answer, correct_answer, is_correct):
    """Save user's answer result"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO results 
                    (user_id, russian_word, user_answer, correct_answer, is_correct)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, russian_word, user_answer, correct_answer, is_correct))
                conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Database error in save_answer_result: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Я бот для изучения английских слов.\n"
        "Используй /cards для начала обучения.\n"
        "Добавляй свои слова с 'Добавить слово ➕' и удаляй с 'Удалить слово🔙'.\n"
        "Используй /cancel для отмены текущего действия."
    )

@bot.message_handler(commands=['cancel'])
def cancel(message):
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "Действие отменено. Используйте /cards для начала.")

@bot.message_handler(commands=['cards'])
def start_bot(message):
    if not check_db_connection():
        bot.send_message(
            message.chat.id,
            "⚠️ Ошибка подключения к базе данных. Пожалуйста, попробуйте позже."
        )
        return

    user_id = message.from_user.id
    word_pair = get_random_word(user_id)
    if not word_pair:
        bot.send_message(
            message.chat.id,
            "В базе нет слов! Добавьте свои слова с 'Добавить слово ➕'"
        )
        return

    russian_word, target_word = word_pair
    markup = generate_question_markup(user_id, russian_word, target_word)
    if not markup:
        bot.send_message(
            message.chat.id,
            "Недостаточно слов для создания вопроса! Добавьте больше слов с 'Добавить слово ➕'."
        )
        return

    bot.send_message(
        message.chat.id,
        f"Как переводится слово '{russian_word}'?",
        reply_markup=markup
    )

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = russian_word

def generate_question_markup(user_id, russian_word, correct_answer):
    """Generate reply keyboard markup with answer options"""
    try:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        other_words = get_random_english_words(user_id, correct_answer, 3)
        
        if len(other_words) < 3:
            logger.warning(f"Insufficient words for quiz: got {len(other_words)} incorrect options for user_id={user_id}")
            return None

        buttons = [types.KeyboardButton(correct_answer)] + \
                 [types.KeyboardButton(word) for word in other_words]
        random.shuffle(buttons)
        markup.add(*buttons)
        markup.add(
            types.KeyboardButton(Command.NEXT),
            types.KeyboardButton(Command.ADD_WORD),
            types.KeyboardButton(Command.DELETE_WORD)
        )
        return markup
    except Exception as e:
        logger.error(f"Error generating markup: {e}")
        return None

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def handle_next(message):
    start_bot(message)

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def handle_add_word(message):
    logger.debug(f"handle_add_word: Setting state to add_russian for user_id={message.from_user.id}")
    bot.send_message(message.chat.id, "Введите слово на русском:")
    bot.set_state(message.from_user.id, MyStates.add_russian, message.chat.id)

@bot.message_handler(func=lambda message: True, state=MyStates.add_russian)
def handle_add_russian(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not message.text.strip():
        bot.send_message(chat_id, "Ошибка: слово не может быть пустым. Попробуйте снова.")
        return
    logger.debug(f"handle_add_russian: Received Russian word '{message.text}' for user_id={user_id}")
    with bot.retrieve_data(user_id, chat_id) as data:
        data['add_russian'] = message.text
    bot.send_message(chat_id, "Введите перевод на английском:")
    bot.set_state(user_id, MyStates.add_english, chat_id)

@bot.message_handler(func=lambda message: True, state=MyStates.add_english)
def handle_add_english(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not message.text.strip():
        bot.send_message(chat_id, "Ошибка: слово не может быть пустым. Попробуйте снова.")
        return
    logger.debug(f"handle_add_english: Received English word '{message.text}' for user_id={user_id}")
    with bot.retrieve_data(user_id, chat_id) as data:
        russian_word = data.get('add_russian')
        english_word = message.text
        if add_user_word(user_id, russian_word, english_word):
            bot.send_message(chat_id, "✅ Слово успешно добавлено!")
        else:
            bot.send_message(
                chat_id,
                "❌ Слово уже существует в вашем словаре."
            )
    bot.delete_state(user_id, chat_id)

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def handle_delete_word(message):
    logger.debug(f"handle_delete_word: Setting state to delete_word for user_id={message.from_user.id}")
    bot.send_message(message.chat.id, "Введите русское слово для удаления:")
    bot.set_state(message.from_user.id, MyStates.delete_word, message.chat.id)

@bot.message_handler(func=lambda message: True, state=MyStates.delete_word)
def handle_delete_russian(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    russian_word = message.text.strip()
    if not russian_word:
        bot.send_message(chat_id, "Ошибка: слово не может быть пустым. Попробуйте снова.")
        return
    logger.debug(f"handle_delete_russian: Attempting to delete Russian word '{russian_word}' for user_id={user_id}")
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_words WHERE user_id = %s AND russian = %s
                    RETURNING id
                """, (user_id, russian_word))
                if cursor.fetchone():
                    bot.send_message(chat_id, "✅ Слово успешно удалено!")
                else:
                    bot.send_message(chat_id, "❌ Слово не найдено в вашем словаре.")
                conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Database error in handle_delete_russian: {e}")
        bot.send_message(chat_id, "❌ Ошибка при удалении слова.")
    bot.delete_state(user_id, chat_id)

@bot.message_handler(func=lambda message: True)
def check_answer(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text in [Command.NEXT, Command.ADD_WORD, Command.DELETE_WORD]:
        logger.debug(f"Skipping check_answer for command: {message.text}")
        return

    current_state = bot.get_state(user_id, chat_id)
    if current_state in [MyStates.add_russian, MyStates.add_english, MyStates.delete_word]:
        logger.debug(f"Skipping check_answer for user_id={user_id}, state={current_state}")
        return

    with bot.retrieve_data(user_id, chat_id) as data:
        if not data:
            bot.send_message(chat_id, "No active question. Use /cards to start.")
            return
        correct_answer = data.get('target_word')
        russian_word = data.get('translate_word')

    if not correct_answer or not russian_word:
        bot.send_message(chat_id, "No active question. Use /cards to start.")
        return

    user_answer = message.text.strip()
    is_correct = user_answer.lower() == correct_answer.lower()

    if is_correct:
        bot.send_message(chat_id, "✅ Correct! Great job!")
        save_answer_result(user_id, russian_word, user_answer, correct_answer, is_correct)
        start_bot(message)
    else:
        bot.send_message(
            chat_id,
            "❌ Неправильно! Попробуйте снова."
        )
        save_answer_result(user_id, russian_word, user_answer, correct_answer, is_correct)
        markup = generate_question_markup(user_id, russian_word, correct_answer)
        if markup:
            bot.send_message(
                chat_id,
                f"Как переводится слово '{russian_word}'?",
                reply_markup=markup
            )

if __name__ == '__main__':
    if check_db_connection():
        logger.info("Database connection established. Starting bot...")
        bot.polling(none_stop=True)
    else:
        logger.error("Failed to connect to database or tables are missing. Exiting...")