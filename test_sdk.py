import sys
import os

# Add libs to path to import local notify-python package
sys.path.append(os.path.join(os.path.dirname(__file__), 'libs/notify-python'))

from notify_python import NotifyClient

def run_demo():
    print("Initializing NotifyClient...")
    client = NotifyClient(
        base_url="http://localhost:8000",
        api_key="dev-key-123"
    )
    
    print("Sending test notification to 'user_123'...")
    try:
        response = client.send_notification(
            channel="user_123",
            title="System Alert",
            body="This is a test notification sent via the Python SDK client!",
            payload={
                "alert_level": "info",
                "triggered_by": "demonstration_script"
            }
        )
        print("Notification Sent Successfully!")
        print("Response:", response)
    except Exception as e:
        print("Failed to send notification:", e)

if __name__ == '__main__':
    run_demo()
