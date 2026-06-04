import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Determine environment
IS_CLOUD_RUN = os.getenv('K_SERVICE') is not None

# Try loading from various possible locations for the .env file
dotenv_locations = []
if IS_CLOUD_RUN:
    dotenv_locations.append(os.path.join('/keys', '.env'))
    
dotenv_locations.extend([
    os.path.join(os.path.dirname(__file__), 'keys', '.env'), # Local dev (relative to file)
    os.path.join(os.getcwd(), 'keys', '.env'),              # Docker /app/keys/
])

for loc in dotenv_locations:
    if os.path.exists(loc):
        load_dotenv(loc)
        break
else:
    load_dotenv() # Fallback to default behavior

# Set Google credentials if they exist
gcp_cred_path = '/keys/service_account.json' if IS_CLOUD_RUN else os.path.join(os.getcwd(), 'keys', 'service_account.json')
if os.path.exists(gcp_cred_path):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_cred_path

import urllib.parse

# MySQL connection settings
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DB = os.getenv("MYSQL_DB", "garden_db")
# The Cloud SQL instance connection name (e.g., project:region:instance)
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "crawler-488903:us-central1:care-my-plants-v2")

encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)

if IS_CLOUD_RUN:
    # On Cloud Run, connect via the Unix socket provided by the Cloud SQL Auth Proxy
    # This avoids public IP timeouts and is more secure.
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@/{MYSQL_DB}"
        f"?unix_socket=/cloudsql/{INSTANCE_CONNECTION_NAME}"
    )
    print(f"Connecting to Cloud SQL via Unix socket: {INSTANCE_CONNECTION_NAME}")
else:
    # Local development or other environments use standard TCP
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"
    print(f"Connecting to MySQL via TCP: {MYSQL_HOST}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    connect_args={"connect_timeout": 5, "read_timeout": 5, "write_timeout": 5}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
