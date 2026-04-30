import sqlalchemy
from database import engine

def patch_db():
    with engine.connect() as conn:
        try:
            conn.execute(sqlalchemy.text("ALTER TABLE gardens ADD COLUMN location VARCHAR(255) DEFAULT 'Bangalore'"))
            print("Added location column.")
        except sqlalchemy.exc.OperationalError as e:
            print(f"Location column might already exist: {e}")
            
        try:
            conn.execute(sqlalchemy.text("ALTER TABLE gardens ADD COLUMN last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            print("Added last_accessed_at column.")
        except sqlalchemy.exc.OperationalError as e:
            print(f"last_accessed_at column might already exist: {e}")

        conn.commit()

if __name__ == "__main__":
    patch_db()
