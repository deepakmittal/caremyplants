import os
import sys
from sqlalchemy import create_engine, text

def main():
    url = "mysql+pymysql://root:Summer%4069@35.232.43.185/garden"
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            # Query garden updates details
            result = conn.execute(
                text("SELECT id, garden_id, status, summary, recommendation, immediate_changes, created_at FROM garden_updates WHERE id IN (42, 43)")
            ).fetchall()
            for r in result:
                print(f"Update ID: {r[0]}, Garden: {r[1]}, Status: {r[2]}")
                print(f"  Summary: {r[3]}")
                print(f"  Recommendation: {r[4]}")
                print(f"  Immediate Changes: {r[5]}")
                print(f"  Created At: {r[6]}")
                print("-" * 50)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
