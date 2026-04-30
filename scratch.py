from database import SessionLocal
import models

db = SessionLocal()
garden = db.query(models.Garden).filter(models.Garden.id == 53).first()
if garden:
    print("Found garden, deleting...")
    db.delete(garden)
    db.commit()
    print("Deleted successfully!")
else:
    print("Garden 53 not found.")
db.close()
