from fastapi import APIRouter, HTTPException, Form
from jose import jwt
from datetime import datetime, timedelta
from app.schemas.token import Token

router = APIRouter()

SECRET_KEY = "supersecret"  # move to env later
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60

@router.post("/token", response_model=Token)
def login(username: str = Form(...), email: str = Form(...)):
    user_data = {"sub": username, "email": email}
    expiration = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    payload = {**user_data, "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return Token(access_token=token)
