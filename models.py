from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Table, Text, LargeBinary, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

# Junction table for User and Garden
garden_users = Table(
    "garden_users",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("garden_id", Integer, ForeignKey("gardens.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String(50), default="owner"),
    Column("created_at", TIMESTAMP, default=datetime.datetime.utcnow)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(255), unique=True, index=True, nullable=False)
    user_phone = Column(String(20))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    gardens = relationship("Garden", secondary=garden_users, back_populates="users")

class Garden(Base):
    __tablename__ = "gardens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # Status lifecycle: 'New' -> 'Processing Garden' -> 'Processing Plants' -> 'Ready'
    status = Column(String(50), default="New", nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    users = relationship("User", secondary=garden_users, back_populates="gardens")
    plants = relationship("Plant", back_populates="garden", cascade="all, delete-orphan")
    updates = relationship("GardenUpdate", back_populates="garden", cascade="all, delete-orphan")
    photos = relationship("GardenPhoto", back_populates="garden", cascade="all, delete-orphan")
    location = Column(String(512))
    summary = Column(String(512))
    upload_commentry = Column(String(512))
    last_accessed_at = Column(TIMESTAMP)

class Plant(Base):
    __tablename__ = "plants"
    id = Column(Integer, primary_key=True, index=True)
    garden_id = Column(Integer, ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    plant_variety = Column(String(255))
    condition = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    image_url = Column(String(512)) # Path in GCS

    garden = relationship("Garden", back_populates="plants")
    updates = relationship("PlantUpdate", back_populates="plant", cascade="all, delete-orphan")

class GardenUpdate(Base):
    __tablename__ = "garden_updates"
    id = Column(Integer, primary_key=True, index=True)
    garden_id = Column(Integer, ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False)
    # Status lifecycle: 'New' -> 'Processing Garden' -> 'Processing Plants' -> 'Ready'
    status = Column(String(50), default="New", nullable=False)
    recommendation = Column(Text)
    summary = Column(String(512))
    upload_commentry = Column(String(512))
    hydration = Column(String(255))
    exposure = Column(String(255))
    vibrancy = Column(String(255))
    temperature = Column(String(255))
    humidity = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    needs_water = Column(Boolean, default=False)
    pest_detected = Column(Boolean, default=False)
    low_sunlight = Column(Boolean, default=False)

    garden = relationship("Garden", back_populates="updates")
    photos = relationship("GardenPhoto", back_populates="update")

class GardenPhoto(Base):
    __tablename__ = "garden_photos"
    id = Column(Integer, primary_key=True, index=True)
    garden_id = Column(Integer, ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False)
    update_id = Column(Integer, ForeignKey("garden_updates.id", ondelete="SET NULL"), nullable=True)
    photo_url = Column(String(512), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

    garden = relationship("Garden", back_populates="photos")
    update = relationship("GardenUpdate", back_populates="photos")

class PlantUpdate(Base):
    __tablename__ = "plant_updates"
    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False)
    condition_text = Column(Text)
    recommendation = Column(Text)
    image_url = Column(String(512))
    # Status lifecycle: 'New' -> 'Processing' -> 'Ready'
    status = Column(String(50), default="New", nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    plant = relationship("Plant", back_populates="updates")
