import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from db.database import get_db
from db import models, schemas

# Secret configuration
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkeyformigration")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Read token from Authorization Header or Cookie (for Admin Dashboard)
async def get_current_user(
    request: Request,
    response: Response = None,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    is_cookie_auth = False
    # Try reading token from cookie if not in authorization header
    if not token:
        token = request.cookies.get("admin_token")
        if token:
            is_cookie_auth = True
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        # Try utilizing refresh token if no access token is present
        refresh_token = request.cookies.get("admin_refresh_token")
        if refresh_token:
            try:
                payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                if payload.get("type") == "refresh":
                    username = payload.get("sub")
                    if username:
                        new_access_token = create_access_token(data={"sub": username})
                        if response:
                            response.set_cookie(
                                key="admin_token",
                                value=new_access_token,
                                httponly=True,
                                max_age=3600 * 24,  # 1 day access cookie expiration
                                samesite="lax",
                                secure=False
                            )
                        token = new_access_token
                        is_cookie_auth = True
            except JWTError:
                pass

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or payload.get("type", "access") != "access":
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        # If access token has expired/invalid, try using refresh token
        if is_cookie_auth:
            refresh_token = request.cookies.get("admin_refresh_token")
            if refresh_token:
                try:
                    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                    if payload.get("type") == "refresh":
                        username = payload.get("sub")
                        if username:
                            new_access_token = create_access_token(data={"sub": username})
                            if response:
                                response.set_cookie(
                                    key="admin_token",
                                    value=new_access_token,
                                    httponly=True,
                                    max_age=3600 * 24,
                                    samesite="lax",
                                    secure=False
                                )
                            user = db.query(models.User).filter(models.User.username == username).first()
                            if user:
                                return user
                except JWTError:
                    pass
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user
