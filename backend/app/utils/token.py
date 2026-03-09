from jose import jwt
from datetime import datetime, timedelta
import os  
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def create_verification_token(email: str):

    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token

# import secrets
# print(secrets.token_hex(32)) //for generate secret key