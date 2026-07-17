import os
import sys
import datetime
from sqlalchemy import create_engine, text

def main():
    url = "mysql+pymysql://root:Summer%4069@35.232.43.185/garden"
    print(f"Connecting to local MySQL: {url}")
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            print("Connected successfully!")
            
            # Current time (local/UTC)
            now = datetime.datetime.utcnow()
            sixteen_hours_ago = now - datetime.timedelta(hours=16)
            print(f"Current UTC time: {now}")
            print(f"Sixteen hours ago UTC: {sixteen_hours_ago}")
            
            # Query garden updates
            print("\n--- Garden Updates ---")
            g_updates = conn.execute(
                text("SELECT id, garden_id, status, summary, created_at FROM garden_updates WHERE created_at >= :t"),
                {"t": sixteen_hours_ago}
            ).fetchall()
            print(f"Found {len(g_updates)} garden updates:")
            for gu in g_updates:
                print(f"  ID: {gu[0]}, Garden: {gu[1]}, Status: {gu[2]}, Created: {gu[4]}")
                
            # Query plant updates
            print("\n--- Plant Updates ---")
            p_updates = conn.execute(
                text("SELECT id, plant_id, status, created_at FROM plant_updates WHERE created_at >= :t"),
                {"t": sixteen_hours_ago}
            ).fetchall()
            print(f"Found {len(p_updates)} plant updates:")
            for pu in p_updates:
                print(f"  ID: {pu[0]}, Plant: {pu[1]}, Status: {pu[2]}, Created: {pu[3]}")
                
            # Query visualizations
            print("\n--- Visualizations ---")
            vis = conn.execute(
                text("SELECT id, garden_id, created_at FROM garden_visualizations WHERE created_at >= :t"),
                {"t": sixteen_hours_ago}
            ).fetchall()
            print(f"Found {len(vis)} visualizations:")
            for v in vis:
                print(f"  ID: {v[0]}, Garden: {v[1]}, Created: {v[2]}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    main()
