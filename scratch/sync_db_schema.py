from database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        commands = [
            # Gardens table
            "ALTER TABLE gardens ADD COLUMN status VARCHAR(50) DEFAULT 'New'",
            "ALTER TABLE gardens ADD COLUMN summary VARCHAR(512)",
            "ALTER TABLE gardens ADD COLUMN location VARCHAR(512)",
            "ALTER TABLE gardens ADD COLUMN upload_commentry VARCHAR(512)",
            "ALTER TABLE gardens ADD COLUMN last_accessed_at TIMESTAMP NULL",
            
            # Garden updates table
            "ALTER TABLE garden_updates ADD COLUMN summary VARCHAR(512)",
            "ALTER TABLE garden_updates ADD COLUMN immediate_changes TEXT",
            "ALTER TABLE garden_updates ADD COLUMN disease_overview TEXT",
            "ALTER TABLE garden_updates ADD COLUMN growth_trend TEXT",
            "ALTER TABLE garden_updates ADD COLUMN upload_commentry VARCHAR(512)",
            "ALTER TABLE garden_updates ADD COLUMN hydration VARCHAR(255)",
            "ALTER TABLE garden_updates ADD COLUMN exposure VARCHAR(255)",
            "ALTER TABLE garden_updates ADD COLUMN vibrancy VARCHAR(255)",
            "ALTER TABLE garden_updates ADD COLUMN temperature VARCHAR(255)",
            "ALTER TABLE garden_updates ADD COLUMN humidity VARCHAR(255)",
            
            # Plants table
            "ALTER TABLE plants ADD COLUMN image_url VARCHAR(512)",
            
            # Fix NULL created_at
            "UPDATE gardens SET created_at = NOW() WHERE created_at IS NULL",
            "UPDATE garden_updates SET created_at = NOW() WHERE created_at IS NULL",
            "UPDATE plants SET created_at = NOW() WHERE created_at IS NULL",
            "UPDATE plant_updates SET created_at = NOW() WHERE created_at IS NULL",
            "UPDATE users SET created_at = NOW() WHERE created_at IS NULL",
            "UPDATE garden_photos SET created_at = NOW() WHERE created_at IS NULL"
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
