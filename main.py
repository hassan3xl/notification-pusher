import os
import uvicorn
import socketio
from fastapi import FastAPI, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db.database import engine, get_db, Base
from socket_manager import sio
from db import models
from controllers import auth

# Import APIRouters
from routes.auth import router as auth_router
from routes.notifications import router as notifications_router
from routes.admin import router as admin_router

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# Setup root admin user automatically if none exist (for dashboard login)
def seed_admin_user():
    db = next(get_db())
    try:
        admin_user = db.query(models.User).filter(models.User.is_admin == True).first()
        if not admin_user:
            print("No admin user found. Creating default admin user...")
            hashed_pwd = auth.get_password_hash("admin123")
            default_admin = models.User(
                username="admin",
                hashed_password=hashed_pwd,
                is_admin=True
            )
            db.add(default_admin)
            db.commit()
            print("Default admin created (username: 'admin', password: 'admin123')")
    except Exception as e:
        print(f"Failed to seed default admin: {e}")
    finally:
        db.close()

seed_admin_user()

# Initialize FastAPI App
app = FastAPI(
    title="Notification Server",
    description="FastAPI + PostgreSQL + Redis Notification microservice with Admin Dashboard",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(admin_router)

# Template Engine Configuration
templates = Jinja2Templates(directory="templates")

# --- Admin Dashboard Web Views ---

@app.get("/", response_class=RedirectResponse)
def root_redirect():
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin", response_class=HTMLResponse)
async def get_admin_dashboard(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("admin_token")
    if not token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    try:
        # Verify user is valid
        current_user = await auth.get_current_user(request, token=token, db=db)
    except Exception:
        # Clean token cookie if verification fails
        response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie("admin_token")
        return response
        
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"user": current_user}
    )

@app.get("/admin/login", response_class=HTMLResponse)
def get_admin_login(request: Request, error: str = None):
    token = request.cookies.get("admin_token")
    if token:
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": error})

@app.post("/admin/login", response_class=HTMLResponse)
def post_admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html", 
            context={"error": "Invalid username or password."}
        )
    
    token = auth.create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=3600 * 24,  # 1 day expiration
        samesite="lax",
        secure=False        # Set to True if using HTTPS
    )
    return response

@app.get("/admin/register", response_class=HTMLResponse)
def get_admin_register(request: Request):
    token = request.cookies.get("admin_token")
    if token:
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="register.html", context={"error": None, "success": None})

@app.post("/admin/register", response_class=HTMLResponse)
def post_admin_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username is already registered.", "success": None}
        )
    
    # Hash password using native bcrypt
    hashed_pwd = auth.get_password_hash(password)
    
    # Check if we want to make it an admin (if no users exist, make admin)
    user_count = db.query(models.User).count()
    is_admin = True if user_count == 0 else False
    
    new_user = models.User(
        username=username,
        hashed_password=hashed_pwd,
        is_admin=is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": None, "success": "Account created successfully! You can now sign in."}
    )

@app.get("/admin/logout", response_class=RedirectResponse)
def get_admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_token")
    return response

# Wrap FastAPI app with Socket.IO ASGIApp to run together on port 8000
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == '__main__':
    uvicorn.run("main:socket_app", host="0.0.0.0", port=8000, reload=True)