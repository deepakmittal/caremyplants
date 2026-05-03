import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Try loading from various possible locations for the .env file
dotenv_locations = [
    os.path.join('/keys', '.env'),                          # Cloud Run mount
    os.path.join(os.path.dirname(__file__), 'keys', '.env'), # Local dev (relative to file)
    os.path.join(os.getcwd(), 'keys', '.env'),              # Docker /app/keys/
]

for loc in dotenv_locations:
    if os.path.exists(loc):
        load_dotenv(loc)
        break
else:
    load_dotenv() # Fallback to default behavior

# Set Google credentials if they exist in the /keys mount
gcp_cred_path = '/keys/service_account.json'
if os.path.exists(gcp_cred_path):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_cred_path

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
