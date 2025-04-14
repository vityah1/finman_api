import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret")
JWT_ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid JWT token: missing subject")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")

def create_access_token(data: dict):
    return jwt.encode(data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
