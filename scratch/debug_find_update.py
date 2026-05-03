import os
from database import SessionLocal
import models
from dotenv import load_dotenv

load_dotenv()

def debug_find():
    db = SessionLocal()
    print(f"Checking database...")
    updates = db.query(models.GardenUpdate).all()
    print(f"Total updates: {len(updates)}")
    for u in updates:
        print(f"ID: {u.id}, Status: '{u.status}'")
    
    pending = db.query(models.GardenUpdate).filter(models.GardenUpdate.status == "Ready to Process").all()
    print(f"Pending 'Ready to Process': {len(pending)}")
    db.close()

if __name__ == "__main__":
    debug_find()
