"""Creates the tables (SQL) or indexes (MongoDB): python -m scripts.migrate"""
from app.config import cfg
from app.db import connect

if __name__ == "__main__":
    cfg.validate()
    db = connect()
    db.migrate()
    db.close()
    print("Database is ready.")
