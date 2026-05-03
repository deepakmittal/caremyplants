from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Garden table columns
    columns_to_add = [
        ("gardens", "location", "VARCHAR(512)"),
        ("gardens", "upload_commentry", "VARCHAR(512)"),
        ("gardens", "last_accessed_at", "TIMESTAMP"),
        ("garden_updates", "upload_commentry", "VARCHAR(512)"),
        ("garden_updates", "hydration", "VARCHAR(255)"),
        ("garden_updates", "exposure", "VARCHAR(255)"),
        ("garden_updates", "vibrancy", "VARCHAR(255)"),
    ]

    for table, col, col_type in columns_to_add:
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};"))
            print(f"Added {col} to {table}")
        except Exception as e:
            print(f"Column {col} in {table} maybe exists or error: {e}")

    conn.commit()
    print("Database updated.")
