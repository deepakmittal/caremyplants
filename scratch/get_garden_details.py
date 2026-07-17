import os
import sys
import datetime
from sqlalchemy import create_engine, text

def main():
    url = "mysql+pymysql://root:Summer%4069@35.232.43.185/garden"
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            # Current time (local/UTC)
            now = datetime.datetime.utcnow()
            sixteen_hours_ago = now - datetime.timedelta(hours=16)
            print(f"Current UTC time: {now}")
            print(f"Sixteen hours ago UTC: {sixteen_hours_ago}")
            
            # Query garden updates in last 16 hours
            g_updates = conn.execute(
                text("SELECT id, garden_id, status, created_at FROM garden_updates WHERE created_at >= :t"),
                {"t": sixteen_hours_ago}
            ).fetchall()
            
            print(f"\nFound {len(g_updates)} garden updates since 16 hours ago:")
            for gu in g_updates:
                uid, gid, status, created_at = gu
                print(f"\n==========================================")
                print(f"Garden Update ID: {uid} | Garden ID: {gid} | Status: {status} | Created: {created_at}")
                
                # Photos
                photos = conn.execute(
                    text("SELECT id, photo_url FROM garden_photos WHERE update_id = :uid"),
                    {"uid": uid}
                ).fetchall()
                print(f"  Photos ({len(photos)}):")
                for p in photos:
                    print(f"    - ID: {p[0]}, URL: {p[1]}")
                    
                # Plant updates
                p_updates = conn.execute(
                    text("SELECT pu.id, p.name, pu.status, pu.created_at FROM plant_updates pu JOIN plants p ON pu.plant_id = p.id WHERE p.garden_id = :gid AND pu.created_at >= :t"),
                    {"gid": gid, "t": sixteen_hours_ago}
                ).fetchall()
                print(f"  Plant Updates ({len(p_updates)}):")
                for pu in p_updates:
                    print(f"    - Update ID: {pu[0]}, Plant Name: '{pu[1]}', Status: {pu[2]}, Created: {pu[3]}")
                    
                # Visualizations
                vis = conn.execute(
                    text("SELECT id, image_url, created_at FROM garden_visualizations WHERE garden_id = :gid"),
                    {"gid": gid}
                ).fetchall()
                print(f"  Visualizations ({len(vis)}):")
                for v in vis:
                    print(f"    - ID: {v[0]}, URL: {v[1]}, Created: {v[2]}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
