import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from db.database import get_db
from config.limiter import r
from db import models, schemas
from controllers import auth

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Dashboard"])

@router.get("/stats")
def get_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_admin:
        # System-wide metrics
        total_users = db.query(models.User).count()
        active_keys = db.query(models.ApiKey).filter(models.ApiKey.is_active == True).count()
        total_notifications = db.query(models.Notification).count()
        sent_notifications = db.query(models.Notification).filter(models.Notification.status == "sent").count()
        read_notifications = db.query(models.Notification).filter(models.Notification.status == "read").count()
        failed_notifications = db.query(models.Notification).filter(models.Notification.status == "failed").count()
        pending_notifications = db.query(models.Notification).filter(models.Notification.status == "pending").count()
        
        try:
            active_websockets = r.scard("sio:active_connections")
        except Exception as e:
            print(f"Failed to query active sockets from Redis: {e}")
            active_websockets = 0
            
        return {
            "users": total_users,
            "active_keys": active_keys,
            "notifications": {
                "total": total_notifications,
                "sent": sent_notifications,
                "read": read_notifications,
                "failed": failed_notifications,
                "pending": pending_notifications
            },
            "active_connections": active_websockets
        }
    else:
        # Client-specific metrics (filtered by client's username as the channel)
        active_keys = db.query(models.ApiKey).filter(models.ApiKey.owner_id == current_user.id, models.ApiKey.is_active == True).count()
        total_notifications = db.query(models.Notification).filter(models.Notification.channel == current_user.username).count()
        sent_notifications = db.query(models.Notification).filter(models.Notification.channel == current_user.username, models.Notification.status == "sent").count()
        read_notifications = db.query(models.Notification).filter(models.Notification.channel == current_user.username, models.Notification.status == "read").count()
        failed_notifications = db.query(models.Notification).filter(models.Notification.channel == current_user.username, models.Notification.status == "failed").count()
        pending_notifications = db.query(models.Notification).filter(models.Notification.channel == current_user.username, models.Notification.status == "pending").count()
        
        return {
            "users": 1,
            "active_keys": active_keys,
            "notifications": {
                "total": total_notifications,
                "sent": sent_notifications,
                "read": read_notifications,
                "failed": failed_notifications,
                "pending": pending_notifications
            },
            "active_connections": 0
        }

@router.get("/api-keys", response_model=list[schemas.ApiKeyResponse])
def list_keys(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_admin:
        return db.query(models.ApiKey).order_by(models.ApiKey.created_at.desc()).all()
    else:
        return db.query(models.ApiKey).filter(models.ApiKey.owner_id == current_user.id).order_by(models.ApiKey.created_at.desc()).all()

@router.post("/api-keys", response_model=schemas.ApiKeyResponse)
def create_key(
    key_in: schemas.ApiKeyCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Generate a unique API key prefix-based token
    raw_key = f"np_{secrets.token_hex(24)}"
    
    db_key = models.ApiKey(
        key=raw_key,
        name=key_in.name,
        owner_id=current_user.id,
        is_active=True
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

@router.post("/api-keys/{key_id}/revoke", response_model=schemas.ApiKeyResponse)
def revoke_key(
    key_id: int, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    api_key_entry = db.query(models.ApiKey).filter(models.ApiKey.id == key_id).first()
    if not api_key_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )
    if not current_user.is_admin and api_key_entry.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke this key"
        )
    api_key_entry.is_active = False
    db.commit()
    db.refresh(api_key_entry)
    return api_key_entry
