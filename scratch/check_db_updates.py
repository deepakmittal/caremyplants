from database import SessionLocal
import models

def main():
    db = SessionLocal()
    try:
        update = db.query(models.GardenUpdate).filter(models.GardenUpdate.id == 34).first()
        if update:
            print("Update 34:")
            print("  status:", update.status)
            print("  summary:", update.summary)
            print("  upload_commentry:", update.upload_commentry)
            print("  created_at:", update.created_at)
        else:
            print("Update 34 not found in database.")
            
        # Let's print the latest 5 updates
        print("\nLatest 5 updates in DB:")
        updates = db.query(models.GardenUpdate).order_by(models.GardenUpdate.created_at.desc()).limit(5).all()
        for u in updates:
            print(f"  ID: {u.id}, status: {u.status}, created_at: {u.created_at}, commentry: {u.upload_commentry}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
