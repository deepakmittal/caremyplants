from database import SessionLocal
import models
db = SessionLocal()
try:
    num_gardens = db.query(models.Garden).delete()
    num_plants = db.query(models.Plant).delete()
    num_users = db.query(models.User).delete()
    db.commit()
    print(f"Deleted {num_gardens} gardens, {num_plants} plants, {num_users} users")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
