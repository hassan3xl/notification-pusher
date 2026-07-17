import os
import redis
import socketio

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
r = redis.from_url(REDIS_URL)

# Create the Socket.IO Async Server with Redis Manager for multi-process scaling
mgr = socketio.AsyncRedisManager(REDIS_URL)
sio = socketio.AsyncServer(async_mode='asgi', client_manager=mgr, cors_allowed_origins='*')

# Setup Socket.IO Event Handlers
@sio.on('connect')
async def connect(sid, environ):
    try:
        # Keep track of active connections globally in Redis
        r.sadd("sio:active_connections", sid)
    except Exception as e:
        print(f"Error tracking socket connection in Redis: {e}")
    print(f"Client connected: {sid}")

@sio.on('disconnect')
async def disconnect(sid):
    try:
        r.srem("sio:active_connections", sid)
    except Exception as e:
        print(f"Error tracking socket disconnection in Redis: {e}")
    print(f"Client disconnected: {sid}")

@sio.on('subscribe')
async def on_subscribe(sid, data):
    channel = data.get('channel')
    token = data.get('token')  # Can validate JWT token here if needed
    
    if not channel:
        print(f"Subscription failed: no channel provided by client {sid}")
        return
        
    await sio.enter_room(sid, channel)
    print(f"Client {sid} joined room/channel: {channel}")
