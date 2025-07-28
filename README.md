# Telegram Vocabulary Bot

**Telegram Vocabulary Bot** is a chatbot for Telegram designed for learning English vocabulary through interactive tests. The bot allows users to practice translating Russian words into English, add and delete their own words, and track their progress using a PostgreSQL database.

### Setup

Before running the main `bot.py` module, you need to perform the following steps:

1.  **Create a Telegram bot:**
    * Open Telegram, find @BotFather, and use the `/newbot` command to create a bot.
    * Copy the bot token provided by BotFather.

2.  **Create a PostgreSQL database:**
    * Set up a PostgreSQL database server.
    * Run the `init_db.sql` script using the `init_db.py` module to create the necessary tables and populate them with initial data.

3.  **Install the necessary libraries:**
    * Install the required Python packages by running the command:
        `pip install pyTelegramBotAPI psycopg2-binary python-dotenv`

4.  **Configure environment variables:**
    * Create a `.env` file in the root folder of the project with the following variables:

| Variable Name | Description |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | The token for the Telegram bot obtained from BotFather. |
| `NAME_DB` | The name of the PostgreSQL database. |
| `USER_DB` | The username for connecting to the database. |
| `PASSWORD_DB` | The user's password for connecting to the database. |
| `HOST_DB` | The database host (e.g., localhost). |
| `POST_DB` | The port for connecting to the database. |

### Bot Commands

The bot supports the following commands and functions:

* **"/start"**: Displays a welcome message with instructions.
* **"/cards"**: Starts a test with a Russian word and four English translation options.
* **"/cancel"**: Cancels the current action and resets the bot's state.
* **"Добавить слово ➕"**: Initiates the process of adding a new word pair (Russian-English) to the user's dictionary.
* **"Удалить слово🔙"**: Initiates the deletion of a Russian word from the user's dictionary.
* **"Дальше ⏭"**: Moves to the next test question.

**Testing Process:**

The bot displays a random Russian word with four answer options (one correct, three incorrect).
The user selects an option and receives feedback:
* "✅ Correct! Great job!" for a correct answer.
* "❌ Неправильно! Попробуйте снова." for an incorrect answer.
Results are saved to track progress.

**Word Management:**

* **Adding a word:** Enter the Russian word and its English translation.
* **Deleting a word:** Specify the Russian word to be deleted.

### Modules

* **`bot.py`** - The main module for running the bot.
    * **Main functions:**
        * `check_db_connection()`: Checks the database connection and the presence of tables.
        * `get_random_word(user_id)`: Retrieves a random word from the common or user's dictionary.
        * `get_random_english_words(user_id, exclude_word, limit)`: Gets random incorrect answer options.
        * `add_user_word(user_id, russian, english)`: Adds a word to the user's dictionary.
        * `save_answer_result(user_id, russian_word, user_answer, correct_answer, is_correct)`: Saves the test results.
        * `generate_question_markup(user_id, russian_word, correct_answer)`: Creates a keyboard with answer options.
    * **Command handlers:**
        * `/start`: Sends a welcome message.
        * `/cards`: Starts the test.
        * `/cancel`: Cancels the current actions.

* **`init_db.py`** - A utility for initializing the PostgreSQL database.
    * **Main function:**
        * `execute_sql_file(filename)`: Executes the `init_db.sql` script to set up the database schema.

* **`init_db.sql`** - An SQL script for creating the database schema and populating it with initial data.
    * Creates the tables: `words`, `user_words`, `results`.
    * Adds indexes to optimize performance.
    * Inserts 10 initial word pairs (Russian-English).

### Usage

1.  **Running the bot:**
    * Execute the command `python bot.py`.
    * Send `/start` in Telegram to see the welcome message.

2.  **Taking a test:**
    * Send `/cards` to start the test.
    * Choose an answer from the provided options.
    * Use "Дальше ⏭" to move to the next question.

3.  **Managing words:**
    * Press "Добавить слово ➕" to add a new word pair.
    * Press "Удалить слово🔙" to delete a word.
    * Use `/cancel` to cancel the action.

4.  **Error Handling:**
    * Database errors are displayed as: "⚠️ Ошибка подключения к базе данных."
    * Incorrect inputs will prompt messages to try again.
