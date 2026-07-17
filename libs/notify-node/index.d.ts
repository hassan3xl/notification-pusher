export class NotifyClient {
    /**
     * Node.js SDK client for the Notification Server.
     */
    constructor(baseUrl: string, apiKey: string);

    /**
     * Send a notification to a specific channel (e.g. user_id).
     */
    sendNotification(
        channel: string,
        title: string,
        body: string,
        payload?: Record<string, any> | null
    ): Promise<{
        id: string;
        channel: string;
        title: string;
        body: string;
        payload: Record<string, any> | null;
        status: string;
        created_at: string;
        read_at: string | null;
    }>;
}
