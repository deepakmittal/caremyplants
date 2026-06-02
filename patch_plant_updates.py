from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE plant_updates ADD COLUMN changes_from_previous TEXT;"))
        conn.commit()
        print("Column changes_from_previous added successfully to plant_updates!")
except Exception as e:
    print(f"Error: {e}")
