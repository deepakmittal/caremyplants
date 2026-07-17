import sqlalchemy
from sqlalchemy import create_engine
import urllib.parse
import json

MYSQL_USER = "root"
MYSQL_PASSWORD = "Summer@69"
MYSQL_HOST = "35.232.43.185"
MYSQL_DB = "garden"

encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
url = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"

try:
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        print("--- GARDENS ---")
        gardens = conn.execute(sqlalchemy.text("SELECT id, name, status, created_at FROM gardens")).fetchall()
        for g in gardens:
            print(f"Garden ID: {g[0]}, Name: {g[1]}, Status: {g[2]}, Created: {g[3]}")
            
            print(f"  --- GARDEN UPDATES for Garden {g[0]} ---")
            updates = conn.execute(sqlalchemy.text("SELECT id, status, created_at FROM garden_updates WHERE garden_id = :gid ORDER BY created_at DESC"), {"gid": g[0]}).fetchall()
            for u in updates:
                print(f"  Update ID: {u[0]}, Status: {u[1]}, Created: {u[2]}")
                
            print(f"  --- PLANTS for Garden {g[0]} ---")
            plants = conn.execute(sqlalchemy.text("SELECT id, name, `condition` FROM plants WHERE garden_id = :gid"), {"gid": g[0]}).fetchall()
            for p in plants:
                print(f"  Plant ID: {p[0]}, Name: {p[1]}, Condition: {p[2]}")
                
                print(f"    --- PLANT UPDATES for Plant {p[0]} ---")
                p_updates = conn.execute(sqlalchemy.text("SELECT id, status, created_at FROM plant_updates WHERE plant_id = :pid ORDER BY created_at DESC"), {"pid": p[0]}).fetchall()
                for pu in p_updates:
                    print(f"    PlantUpdate ID: {pu[0]}, Status: {pu[1]}, Created: {pu[2]}")
except Exception as e:
    print("Failed:", e)
