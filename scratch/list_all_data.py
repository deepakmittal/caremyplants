import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "garden")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def list_all():
    with engine.connect() as conn:
        print("--- Gardens ---")
        res = conn.execute(text("SELECT id, name, status FROM gardens"))
        for row in res:
            print(row)
            
        print("\n--- Garden Updates ---")
        res = conn.execute(text("SELECT id, garden_id, status, upload_commentry FROM garden_updates"))
        for row in res:
            print(row)
            
        print("\n--- Plants ---")
        res = conn.execute(text("SELECT id, garden_id, name FROM plants"))
        for row in res:
            print(row)

if __name__ == "__main__":
    list_all()
