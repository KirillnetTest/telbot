import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def execute_sql_file(filename):
    conn = None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        for statement in sql.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    execute_sql_file('init_db.sql')