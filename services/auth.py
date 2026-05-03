import os
from sqlalchemy.orm import Session
from models import User
from schemas import UserLogin
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv

# Try loading from various possible locations for the .env file
dotenv_locations = [
    os.path.join('/keys', '.env'),                               # Cloud Run mount
    os.path.join(os.path.dirname(__file__), '..', 'keys', '.env'), # Local dev (one level up)
    os.path.join(os.getcwd(), 'keys', '.env'),                   # Docker /app/keys/
]

for loc in dotenv_locations:
    if os.path.exists(loc):
        load_dotenv(loc)
        break
else:
    load_dotenv() # Fallback to default behavior

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_external_user(db: Session, login_data: UserLogin):
    # In a real app, you would verify the access_token with Google/FB APIs
    # For this implementation, we'll mock the extraction of user data
    print(f"Authenticating with {login_data.provider}...")
    
    # Mock data extraction
    mock_email = f"user_{login_data.provider}@example.com"
    mock_phone = "1234567890"

    # Match email or phone number for uniqueness as requested
    user = db.query(User).filter(
        (User.user_email == mock_email) | (User.user_phone == mock_phone)
    ).first()

    if not user:
        user = User(
            user_email=mock_email,
            user_phone=mock_phone,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = create_access_token({"sub": user.user_email})
    return user, token
