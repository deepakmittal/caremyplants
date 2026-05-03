from database import engine
from sqlalchemy import text

def check():
    with engine.connect() as conn:
        res = conn.execute(text('DESCRIBE gardens'))
        for row in res:
            print(row)

if __name__ == "__main__":
    check()
