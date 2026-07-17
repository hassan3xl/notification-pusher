# notify-python

Python SDK client for the Notification Server. Used by backend applications to push notifications to users.

## Installation

```bash
pip install .
```

## Usage

```python
from notify_python import NotifyClient

# Initialize the client with the server URL and your API Key
client = NotifyClient(
    base_url="http://localhost:8000",
    api_key="your-api-key-here"
)

# Send a notification to a specific channel (e.g. user_id)
response = client.send_notification(
    channel="user_987",
    title="New Message",
    body="You have received a new notification!",
    payload={
        "message_id": "msg_abc123",
        "sender": "System Admin"
    }
)

print(response)
# {
#   "id": "uuid-here",
#   "channel": "user_987",
#   "title": "New Message",
#   "body": "You have received a new notification!",
#   "payload": { ... },
#   "status": "sent",
#   "created_at": "..."
# }
```
