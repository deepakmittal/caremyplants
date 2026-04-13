from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Table, Text, LargeBinary
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
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    users = relationship("User", secondary=garden_users, back_populates="gardens")
    plants = relationship("Plant", back_populates="garden", cascade="all, delete-orphan")
    updates = relationship("GardenUpdate", back_populates="garden", cascade="all, delete-orphan")
    photos = relationship("GardenPhoto", back_populates="garden", cascade="all, delete-orphan")

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

class GardenUpdate(Base):
    __tablename__ = "garden_updates"
    id = Column(Integer, primary_key=True, index=True)
    garden_id = Column(Integer, ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(255))
    recommendation = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.datetime.utcnow)

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
