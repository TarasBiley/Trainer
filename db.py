import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()


def get_db():
    return psycopg2.connect(os.environ['DATABASE_URL'])



def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        sessions INTEGER NOT NULL
    );
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id SERIAL PRIMARY KEY,
        client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        time TIME NOT NULL,
        UNIQUE (date, time)
    );
    ''')

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Таблицы успешно созданы.")

'''
