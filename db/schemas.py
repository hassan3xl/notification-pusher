from pydantic import BaseModel, Field
from typing import Any, Optional, Dict
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    is_admin: Optional[bool] = False

class UserResponse(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(UserBase):
    password: str

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationPushRequest(BaseModel):
    channel: Optional[str] = Field(default=None, description="Optional channel name")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body content")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra custom JSON payload data")

class NotificationResponse(BaseModel):
    id: str
    channel: Optional[str]
    title: str
    body: str
    payload: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    username: Optional[str] = None
