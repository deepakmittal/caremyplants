from sqlalchemy import create_engine, text
import urllib.parse

db_user = "root"
db_password = urllib.parse.quote_plus("Summer@69")
db_host = "127.0.0.1"
db_port = 3307
db_name = "garden"

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

with engine.connect() as conn:
    result = conn.execute(text("DESCRIBE garden_updates;"))
    for row in result:
        print(row)
