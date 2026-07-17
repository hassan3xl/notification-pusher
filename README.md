# Notification Pusher Microservice

A production-grade, highly scalable notification pusher microservice built with **FastAPI**, **Socket.IO (WebSockets)**, **Redis**, **PostgreSQL**, and **Jinja2**.

This microservice acts as a centralized notification dispatcher. Backend applications (such as billing services, user management, or inventory tracking) can push notifications to users via simple REST API calls using provided client SDKs. Client apps or frontends listen in real time over WebSockets to display instant popups/alerts.

---

## Key Features

- ⚡ **Real-Time Delivery**: Built on top of Socket.IO (ASGI) for bidirectional, low-latency, and event-driven communication.
- 🗄️ **Persistent Audit Trail**: Every notification and status transition (pending, sent, read, failed) is stored in a PostgreSQL database.
- 🧠 **Redis State Tracking & Clustering**: Uses Redis Set to track live WebSocket client connections and acts as a Socket.IO message broker.
- 🛠️ **Glassmorphic Admin Dashboard**: A premium, real-time analytics web dashboard showing connection metrics, transmission charts, history logs, and API key management.
- 🔑 **API Key Management**: Create and revoke API access credentials for external caller microservices.
- 🛡️ **JWT Authentication**: Full cookie and bearer-token JWT auth implementation protecting admin views and individual history queries.
- 🚦 **Redis Rate Limiting**: Token-bucket rate limiting (100 requests/min per API Key or IP) to prevent service starvation.
- 📦 **Dockerized Setup**: Seamless orchestration of Python backend, PostgreSQL, and Redis.

---

## Directory Architecture

```text
notification-pusher/
├── config/
│   └── limiter.py           # Redis token-bucket rate limiter middleware
├── controllers/
│   └── auth.py              # Cryptography, JWT signing, & security dependencies
├── db/
│   ├── database.py          # SQLAlchemy PostgreSQL connection settings
│   ├── models.py            # PostgreSQL table schemas (User, ApiKey, Notification)
│   └── schemas.py           # Pydantic validation models
├── libs/
│   ├── notify-node/         # Zero-dependency Node.js client SDK library
│   └── notify-python/       # Lightweight Python client SDK library
├── routes/
│   ├── admin.py             # Analytics statistics & dynamic API keys API
│   ├── auth.py              # JWT authentication endpoints
│   └── notifications.py     # Ingest API (/notify), read markers, client history
├── templates/
│   ├── dashboard.html       # Real-time dashboard view (Socket.IO + Chart.js)
│   └── login.html           # Glassmorphic admin authorization login page
├── Dockerfile               # Slim Debian-based Python container build file
├── docker-compose.yml       # Production-ready compose configuration (DB + Redis + App)
├── entrypoint.sh            # Network dependency checker script (waits for PG + Redis)
├── main.py                  # Server entrypoint (Mounts routers, templates & SIO ASGI)
├── pyproject.toml           # Core dependencies & metadata (using uv)
└── test_sdk.py              # Demonstration script testing local SDK execution
```

---

## Getting Started

### 1. Build and Run the Stack
Start the PostgreSQL, Redis, and FastAPI backend services:
```bash
docker compose up --build -d
```
The application will automatically wait for the database and Redis to accept connections before booting. On the first startup, the microservice will automatically compile all tables and seed a default admin user.

### 2. Access the Admin Dashboard
Open your web browser and navigate to:
- **URL**: [https://notification.qstack.com.ng/admin](https://notification.qstack.com.ng/admin)
- **Default Username**: `admin`
- **Default Password**: `admin123`

---

## API Reference Summary

### Authentication APIs
- `POST /api/v1/auth/register` - Create a user account (The first registered user is granted Admin privileges).
- `POST /api/v1/auth/login` - Authenticate credentials and return a JWT access token.
- `GET /api/v1/auth/me` - Retrieve the current authenticated user's profile info.

### Notification APIs
- `POST /api/v1/notifications/notify` - Dispatch/emit a notification.
  - *Headers*: `X-API-Key: <your_api_key>`
  - *Request Body*:
    ```json
    {
      "channel": "user_123",
      "title": "Invoice Paid",
      "body": "Your invoice for July has been successfully processed.",
      "payload": {
        "invoice_id": "inv_987",
        "amount": 29.99
      }
    }
    ```
- `GET /api/v1/notifications/history` - Retrieve audit trail of sent notifications (Admins see all; users see only their own channel history).
- `POST /api/v1/notifications/{notification_id}/read` - Mark a notification status as `read`.

### Admin Dashboard APIs
- `GET /api/v1/admin/stats` - Fetch real-time counters, active sockets, and status counts.
- `GET /api/v1/admin/api-keys` - List all generated client API keys.
- `POST /api/v1/admin/api-keys` - Generate a new app API key.
- `POST /api/v1/admin/api-keys/{key_id}/revoke` - Instantly revoke access for an API key.

---

## Client SDK Libraries & Usage

### 🐍 Python SDK (`libs/notify-python`)

#### Installation
```bash
pip install ./libs/notify-python
```

#### Usage
```python
from notify_python import NotifyClient

# Initialize the client
client = NotifyClient(
    base_url="https://notification.qstack.com.ng",
    api_key="dev-key-123"  # or generate a custom key from the dashboard
)

# Dispatch notification
response = client.send_notification(
    channel="user_123",
    title="System Alert",
    body="Backup completed successfully.",
    payload={"disk_usage": "42%"}
)

print(response)
```

---

### 🟢 Node.js SDK (`libs/notify-node`)

#### Installation
```bash
npm install ./libs/notify-node
```

#### Usage
```javascript
const { NotifyClient } = require("notify-node");

// Initialize client (requires Node.js v18+)
const client = new NotifyClient("https://notification.qstack.com.ng", "dev-key-123");

async function run() {
  const response = await client.sendNotification(
    "user_123",
    "Deployment Completed",
    "Version 2.4.0 is now live in production.",
    { environment: "production" }
  );
  console.log(response);
}

run();
```
