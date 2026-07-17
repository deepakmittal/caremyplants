import sqlalchemy
from sqlalchemy import create_engine
import urllib.parse

# Production credentials
MYSQL_USER = "root"
MYSQL_PASSWORD = "Summer@69"
MYSQL_HOST = "34.10.240.61"
MYSQL_DB = "garden"

encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
url = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"
print("Connecting...")
try:
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        print("Connected successfully!")
        result = conn.execute(sqlalchemy.text("SELECT 1"))
        print("Query result:", result.fetchone())
except Exception as e:
    print("Connection failed:", e)
