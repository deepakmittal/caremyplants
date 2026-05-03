from database import engine
from sqlalchemy import text

def check():
    with engine.connect() as conn:
        res = conn.execute(text('SELECT * FROM garden_users'))
        for row in res:
            print(row)
        
        res2 = conn.execute(text('SELECT * FROM users'))
        for row in res2:
            print(f"User: {row}")

if __name__ == "__main__":
    check()
