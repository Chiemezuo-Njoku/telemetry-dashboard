import sqlite3
import os

# Store the database file in the root project directory
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "telemetry.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    # Allows accessing columns by name (e.g., row["cpu_usage"])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database and creates the metrics table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            cpu_usage REAL,
            memory_usage REAL,
            available_memory_mb REAL,
            disk_usage REAL,
            gpu_utilization REAL,
            gpu_memory_used_mb REAL,
            gpu_temp_c REAL
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")