import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.orm import Session
from db.database import get_db
from socket_manager import sio
from config.limiter import rate_limiter
from db import models, schemas
from controllers import auth

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

# Load static API keys from environment
VALID_API_KEYS = os.getenv('VALID_API_KEYS', '')
STATIC_API_KEYS = set(VALID_API_KEYS.split(',')) if VALID_API_KEYS else set()

async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key"
        )
    
    # Check static env keys first
    if x_api_key in STATIC_API_KEYS:
        return "system"

    # Check database keys
    api_key_entry = db.query(models.ApiKey).filter(
        models.ApiKey.key == x_api_key,
        models.ApiKey.is_active == True
    ).first()
    
    if not api_key_entry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key"
        )
    return api_key_entry

# --- Ingest REST API (used by other apps) ---
@router.post("/notify", response_model=schemas.NotificationResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(rate_limiter)])
async def notify(
    payload: schemas.NotificationPushRequest,
    api_key_owner = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    # 1. Create notification record in Postgres
    db_notification = models.Notification(
        channel=payload.channel,
        title=payload.title,
        body=payload.body,
        payload=payload.payload,
        status="pending"
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    try:
        # 2. Emit real-time notification to Socket.IO room/channel
        notification_data = {
            "id": db_notification.id,
            "title": db_notification.title,
            "body": db_notification.body,
            "payload": db_notification.payload,
            "channel": db_notification.channel,
            "created_at": db_notification.created_at.isoformat()
        }
        await sio.emit('notification', notification_data, room=payload.channel)
        
        # Broadcast to admin room for real-time dashboard logs
        await sio.emit('admin_notification', {**notification_data, "status": "sent"}, room="admin")
        
        # Update status to sent
        db_notification.status = "sent"
        db.commit()
        db.refresh(db_notification)
    except Exception as e:
        print(f"Error emitting notification: {e}")
        db_notification.status = "failed"
        db.commit()
        db.refresh(db_notification)
        
    return db_notification

# --- Notification History ---
@router.get("/history", response_model=List[schemas.NotificationResponse])
def get_history(
    channel: Optional[str] = Query(None, description="Filter history by channel name/user_id"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Admins can query anything, normal users can only query their own channel/username
    query = db.query(models.Notification)
    
    if not current_user.is_admin:
        # Enforce that normal users can only access notifications destined for their username/channel
        query = query.filter(models.Notification.channel == current_user.username)
    elif channel:
        query = query.filter(models.Notification.channel == channel)
        
    notifications = query.order_by(models.Notification.created_at.desc()).offset(offset).limit(limit).all()
    return notifications

# --- Mark as Read ---
@router.post("/{notification_id}/read", response_model=schemas.NotificationResponse)
def mark_read(
    notification_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
        
    # Security: Ensure client user owns this channel before marking as read (unless admin)
    if not current_user.is_admin and notification.channel != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this notification"
        )
        
    notification.status = "read"
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification
