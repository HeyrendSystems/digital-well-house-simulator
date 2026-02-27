import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sim_data.db"


class SimDatabase:

    def __init__(self):
        self.connection = None

    def init_db(self):
        self.connection = sqlite3.connect(DB_PATH)
        self.create_tables()
        print("Database connected")

    def close_db(self):
        if self.connection:
            print("Database closed")
            self.connection.close()
            self.connection = None

    def wipe_data(self):
        if DB_PATH.exists():
           DB_PATH.unlink()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            flow_gpm REAL,
            pump_head REAL,
            system_head REAL,
            vfd_percent REAL
        )
        """)
        self.connection.commit()

    def insert_reading(self, timestamp, flow_gpm, pump_head, system_head, vfd_percent):
        cursor = self.connection.cursor()
        cursor.execute("""
        INSERT INTO readings(
            timestamp,
            flow_gpm,
            pump_head,
            system_head,
            vfd_percent
        ) VALUES (?, ?, ?, ?, ?)
        """, (timestamp, flow_gpm , pump_head / 10, system_head / 10, vfd_percent))
        self.connection.commit()




