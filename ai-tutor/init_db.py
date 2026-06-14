import sqlite3

conn = sqlite3.connect("database/ai_tutor.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS quiz_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    score INTEGER,
    level TEXT,
    weak_topics TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Quiz history table created successfully")