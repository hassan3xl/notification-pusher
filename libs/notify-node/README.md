# notify-node

Node.js client library for the Notification Server. Used by backend applications to push notifications to users.

## Installation

```bash
npm install ../notify-node
```

## Usage

```javascript
const { NotifyClient } = require("notify-node");

// Initialize the client with the server URL and your API Key
const client = new NotifyClient("http://localhost:8000", "your-api-key-here");

// Send a notification
async function run() {
  try {
    const response = await client.sendNotification(
      "user_987",
      "New Message",
      "You have received a new notification!",
      {
        message_id: "msg_abc123",
        sender: "System Admin"
      }
    );
    console.log("Notification sent successfully:", response);
  } catch (error) {
    console.error("Error sending notification:", error.message);
  }
}

run();
```
