import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import GardenUpdate, PlantUpdate

DATABASE_URL = "mysql+pymysql://root:@localhost/garden"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_status():
    db = SessionLocal()
    print("--- Garden Updates ---")
    updates = db.query(GardenUpdate).all()
    for u in updates:
        print(f"Update ID: {u.id}, Garden ID: {u.garden_id}, Status: {u.status}, Commentary: {u.upload_commentry}")
    
    print("\n--- Plant Updates ---")
    p_updates = db.query(PlantUpdate).all()
    for pu in p_updates:
        print(f"Plant Update ID: {pu.id}, Plant ID: {pu.plant_id}, Status: {pu.status}")
    db.close()

if __name__ == "__main__":
    check_status()
