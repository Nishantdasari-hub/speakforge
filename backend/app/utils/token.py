from datetime import datetime, timedelta
import jwt
from app.config import SECRET_KEY

ALGORITHM = "HS256"


def create_verification_token(email):
    return jwt.encode({"email":email,"purpose":"verify","exp":datetime.utcnow() + timedelta(hours=24)}, SECRET_KEY, algorithm=ALGORITHM)
