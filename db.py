import sqlite3

def get_db():
    conn = sqlite3.connect('db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sessions INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        date TEXT,
        time TEXT,
        UNIQUE (date, time),
        FOREIGN KEY (client_id) REFERENCES clients(id)
    );
    ''')
    db.commit()

if __name__ == '__main__':
    init_db()
