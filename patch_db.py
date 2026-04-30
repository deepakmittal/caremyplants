from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE garden_updates ADD COLUMN upload_commentry VARCHAR(255) NULL;"))
    conn.commit()
    print("Column added successfully!")
