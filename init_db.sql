SET client_min_messages TO WARNING;

CREATE TABLE IF NOT EXISTS words (
    id SERIAL PRIMARY KEY,
    russian TEXT NOT NULL,
    english TEXT NOT NULL,
    CONSTRAINT unique_russian_english UNIQUE (russian, english)
);

CREATE TABLE IF NOT EXISTS user_words (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    russian TEXT NOT NULL,
    english TEXT NOT NULL,
    CONSTRAINT unique_user_russian_english UNIQUE (user_id, russian, english)
);

CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    russian_word TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_words_user_id ON user_words(user_id);
CREATE INDEX IF NOT EXISTS idx_results_user_id ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_words_russian ON words(russian);

INSERT INTO words (russian, english) VALUES
    ('Красный', 'Red'),
    ('Синий', 'Blue'),
    ('Зеленый', 'Green'),
    ('Желтый', 'Yellow'),
    ('Я', 'I'),
    ('Ты', 'You'),
    ('Он', 'He'),
    ('Она', 'She'),
    ('Дом', 'House'),
    ('Машина', 'Car')
ON CONFLICT (russian, english) DO NOTHING;