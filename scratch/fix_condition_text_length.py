from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        commands = [
            "ALTER TABLE plant_updates MODIFY COLUMN condition_text TEXT"
        ]
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                conn.commit()
                print(f"Executed: {cmd}")
            except Exception as e:
                print(f"Skipping {cmd}: {e}")

if __name__ == "__main__":
    migrate()
