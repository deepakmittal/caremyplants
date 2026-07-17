from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE plant_updates ADD COLUMN box_2d VARCHAR(255) NULL;"))
        conn.commit()
        print("Column box_2d added successfully to plant_updates!")
except Exception as e:
    print(f"Error: {e}")
