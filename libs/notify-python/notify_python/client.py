import requests
from typing import Dict, Any, Optional

class NotifyClient:
    """
    Python SDK client for the Notification Server.
    Used by backend applications to push notifications to users.
    """
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the client.
        
        :param base_url: Base URL of the notification server (e.g. 'http://localhost:8000')
        :param api_key: API Key for ingestion authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def send_notification(
        self, 
        channel: str, 
        title: str, 
        body: str, 
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a notification to a specific channel (e.g. user_id).
        
        :param channel: Target channel name or user ID
        :param title: Notification title
        :param body: Notification body/message
        :param payload: Optional custom JSON dict metadata payload
        :return: JSON response dictionary from the server
        """
        url = f"{self.base_url}/api/v1/notifications/notify"
        data = {
            "channel": channel,
            "title": title,
            "body": body,
            "payload": payload or {}
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
