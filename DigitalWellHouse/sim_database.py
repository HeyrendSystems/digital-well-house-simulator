import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sim_data.db"


class SimDatabase:

    def __init__(self):
        self.conn = None

    def init_db(self):
        self.conn = sqlite3.connect(DB_PATH)
        print("Database connected")

    def close_db(self):
        if self.conn:
            print("Database closed")
            self.conn.close()
            self.conn = None
