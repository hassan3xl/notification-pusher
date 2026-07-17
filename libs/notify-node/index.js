class NotifyClient {
    /**
     * Node.js SDK client for the Notification Server.
     * Uses Node's built-in global fetch (requires Node.js v18+).
     * 
     * @param {string} baseUrl - Base URL of the notification server (e.g. 'http://localhost:8000')
     * @param {string} apiKey - API Key for ingestion authentication
     */
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        this.apiKey = apiKey;
    }

    /**
     * Send a notification to a specific channel.
     * 
     * @param {string} channel - Target channel name or user ID
     * @param {string} title - Notification title
     * @param {string} body - Notification body content
     * @param {Record<string, any>} [payload] - Optional custom JSON object payload
     * @returns {Promise<any>}
     */
    async sendNotification(channel, title, body, payload = null) {
        const url = `${this.baseUrl}/api/v1/notifications/notify`;
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-API-Key": this.apiKey,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                channel,
                title,
                body,
                payload: payload || {}
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Notification failed with status ${response.status}: ${errorText}`);
        }

        return response.json();
    }
}

module.exports = { NotifyClient };
