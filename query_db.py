from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, status, upload_commentry FROM garden_updates WHERE id = 50;")).fetchone()
    print(f"Garden Update 50: {result}")
