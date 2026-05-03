import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "garden_db")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        print("Checking garden_updates table columns...")
        columns = [
            ("summary", "VARCHAR(512)"),
            ("immediate_changes", "TEXT"),
            ("disease_overview", "TEXT"),
            ("growth_trend", "TEXT"),
            ("hydration", "VARCHAR(255)"),
            ("exposure", "VARCHAR(255)"),
            ("vibrancy", "VARCHAR(255)"),
            ("temperature", "VARCHAR(255)"),
            ("humidity", "VARCHAR(255)"),
        ]
        
        for col_name, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE garden_updates ADD COLUMN {col_name} {col_type}"))
                print(f"Added column {col_name} to garden_updates.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"Column {col_name} already exists in garden_updates.")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        print("\nChecking gardens table columns...")
        garden_columns = [
            ("location", "VARCHAR(512)"),
            ("summary", "VARCHAR(512)"),
            ("upload_commentry", "VARCHAR(512)"),
            ("last_accessed_at", "TIMESTAMP NULL"),
        ]
        for col_name, col_type in garden_columns:
            try:
                conn.execute(text(f"ALTER TABLE gardens ADD COLUMN {col_name} {col_type}"))
                print(f"Added column {col_name} to gardens.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"Column {col_name} already exists in gardens.")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        conn.commit()
    print("\nMigration complete.")

if __name__ == "__main__":
    migrate()
