import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Try loading from the new 'keys' directory first
dotenv_path = os.path.join(os.path.dirname(__file__), 'keys', '.env')
if not os.path.exists(dotenv_path):
    # Fallback for Docker or when run from root
    dotenv_path = os.path.join(os.getcwd(), 'keys', '.env')

load_dotenv(dotenv_path)

import urllib.parse

# MySQL connection string format: mysql+pymysql://user:password@host:port/dbname
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "garden_db")

encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
