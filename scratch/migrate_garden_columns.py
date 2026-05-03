from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        commands = [
            "ALTER TABLE gardens ADD COLUMN summary VARCHAR(512)",
            "ALTER TABLE garden_updates ADD COLUMN summary VARCHAR(512)",
            "ALTER TABLE garden_updates ADD COLUMN immediate_changes TEXT",
            "ALTER TABLE garden_updates ADD COLUMN disease_overview TEXT",
            "ALTER TABLE garden_updates ADD COLUMN growth_trend TEXT"
        ]
        for cmd in commands:
            try:
                conn.execute(text(cmd))
                print(f"Executed: {cmd}")
            except Exception as e:
                print(f"Skipping {cmd}: {e}")
        conn.commit()

if __name__ == "__main__":
    migrate()
