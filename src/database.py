import sqlite3
import os
from datetime import datetime


class Database:
    def __init__(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(root_dir, "conversations.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                subject TEXT,
                last_message TEXT,
                updated_at DATETIME,
                is_archived INTEGER DEFAULT 0,
                note TEXT DEFAULT ""
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                text TEXT,
                sender TEXT,
                timestamp DATETIME,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        self.conn.commit()

    def create_conversation(self, level, subject):
        cursor = self.conn.cursor()
        now = datetime.now()
        cursor.execute(
            "INSERT INTO conversations (level, subject, last_message, updated_at) VALUES (?, ?, ?, ?)",
            (level, subject, "", now),
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_message(self, conversation_id, text, sender):
        cursor = self.conn.cursor()
        now = datetime.now()
        cursor.execute(
            "INSERT INTO messages (conversation_id, text, sender, timestamp) VALUES (?, ?, ?, ?)",
            (conversation_id, text, sender, now),
        )
        cursor.execute(
            "UPDATE conversations SET last_message = ?, updated_at = ? WHERE id = ?",
            (text, now, conversation_id),
        )
        self.conn.commit()

    def get_conversations(self, archived=False):
        cursor = self.conn.cursor()
        is_archived = 1 if archived else 0
        cursor.execute(
            "SELECT * FROM conversations WHERE is_archived = ? ORDER BY updated_at DESC",
            (is_archived,),
        )
        return cursor.fetchall()

    def get_conversation(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
        return cursor.fetchone()

    def archive_conversation(self, conversation_id, archived=True):
        cursor = self.conn.cursor()
        is_archived = 1 if archived else 0
        cursor.execute(
            "UPDATE conversations SET is_archived = ? WHERE id = ?",
            (is_archived, conversation_id),
        )
        self.conn.commit()

    def update_note(self, conversation_id, note):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE conversations SET note = ? WHERE id = ?", (note, conversation_id)
        )
        self.conn.commit()

    def get_messages(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT text, sender FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,),
        )
        return cursor.fetchall()

    def delete_conversation(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE conversation_id = ?", (conversation_id,)
        )
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        self.conn.commit()
