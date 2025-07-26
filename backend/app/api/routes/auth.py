from fastapi import APIRouter, HTTPException, Form, status
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.schemas.token import Token

router = APIRouter()

SECRET_KEY = "supersecret"  # move to env later
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60


@router.post("/token", response_model=Token)
def login(username: str = Form(...), email: str = Form(...)):
    try:
        # TODO: Add actual user authentication logic here
        # For now, this is a placeholder that accepts any username/email

        user_data = {"sub": username, "email": email}
        expiration = datetime.now(timezone.utc) + timedelta(minutes=EXPIRATION_MINUTES)
        payload = {**user_data, "exp": expiration}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return Token(access_token=token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )
