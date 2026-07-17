import os
import pymysql
from dotenv import load_dotenv

load_dotenv("/Users/ritika/AgentSmith/.env")

user = os.getenv("MYSQL_USER", "root")
password = os.getenv("MYSQL_PASSWORD", "AgentSmith2024!")
host = os.getenv("MYSQL_HOST", "127.0.0.1")
db_name = os.getenv("MYSQL_DB", "garden_dev")

print(f"Connecting to DB {db_name} on {host} as {user}...")

connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=db_name,
    port=3306
)

try:
    with connection.cursor() as cursor:
        # Check if column health_score already exists
        cursor.execute("SHOW COLUMNS FROM garden_updates LIKE 'health_score'")
        res = cursor.fetchone()
        if not res:
            print("Adding health_score column...")
            cursor.execute("ALTER TABLE garden_updates ADD COLUMN health_score INT DEFAULT 3")
        else:
            print("health_score column already exists")

        # Check if column health_metrics already exists
        cursor.execute("SHOW COLUMNS FROM garden_updates LIKE 'health_metrics'")
        res = cursor.fetchone()
        if not res:
            print("Adding health_metrics column...")
            cursor.execute("ALTER TABLE garden_updates ADD COLUMN health_metrics TEXT")
        else:
            print("health_metrics column already exists")
            
        connection.commit()
        print("Success!")
except Exception as e:
    print("Error:", e)
finally:
    connection.close()
