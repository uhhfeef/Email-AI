import sqlite3

def create_database():
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()
    # Create a table for storing email data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmailData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            prediction INT NOT NULL
        )
    ''')
    conn.commit()
    return conn

def insert_email_data(conn, message_id, sender, subject, body, prediction):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO EmailData (message_id, sender, subject, body, prediction) VALUES (?, ?, ?, ?, ?)', 
                   (message_id, sender, subject, body, prediction))
    conn.commit()
