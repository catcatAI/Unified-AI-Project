/**
 * Angela AI Desktop App - API Client
 * Handles communication with backend API server
 */

class AngelaAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.connected = false;
    }

    /**
     * Test connection to backend
     */
    async testConnection() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            this.connected = response.ok;
            return this.connected;
        } catch (error) {
            console.error('Backend connection failed:', error);
            this.connected = false;
            return false;
        }
    }

    /**
     * Send message to Angela
     * @param {string} message - User message
     * @returns {Promise<Object>} Angela's response
     */
    async sendMessage(message) {
        try {
            const response = await fetch(`${this.baseURL}/dialogue`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    user_id: 'desktop_user',
                    session_id: this.getSessionId()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return {
                success: true,
                response: data.response || data.message || 'No response',
                emotion: data.emotion || 'neutral',
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Failed to send message:', error);
            return {
                success: false,
                response: `Error: ${error.message}`,
                emotion: 'confused',
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Get Angela's current status
     * @returns {Promise<Object>} Status data
     */
    async getStatus() {
        try {
            const response = await fetch(`${this.baseURL}/status`);
            const data = await response.json();
            return {
                success: true,
                health: data.health || 100,
                energy: data.energy || 100,
                mood: data.mood || 'happy',
                status: data.status || 'idle'
            };
        } catch (error) {
            console.error('Failed to get status:', error);
            return {
                success: false,
                health: 0,
                energy: 0,
                mood: 'unknown',
                status: 'offline'
            };
        }
    }

    /**
     * Get economy/resource status
     * @returns {Promise<Object>} Economy data
     */
    async getEconomy() {
        try {
            const response = await fetch(`${this.baseURL}/economy/balance`);
            const data = await response.json();
            return {
                success: true,
                coins: data.coins || 0,
                food: data.food || 0,
                energy: data.energy || 0
            };
        } catch (error) {
            console.error('Failed to get economy:', error);
            return {
                success: false,
                coins: 0,
                food: 0,
                energy: 0
            };
        }
    }

    /**
     * Trigger pet action
     * @param {string} action - Action name (e.g., 'feed', 'play', 'rest')
     * @returns {Promise<Object>} Action result
     */
    async triggerAction(action) {
        try {
            const response = await fetch(`${this.baseURL}/pet/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            const data = await response.json();
            return {
                success: true,
                result: data.result || 'Action completed',
                newStatus: data.status || {}
            };
        } catch (error) {
            console.error('Failed to trigger action:', error);
            return {
                success: false,
                result: `Error: ${error.message}`
            };
        }
    }

    /**
     * Get or create session ID
     * @private
     */
    getSessionId() {
        let sessionId = localStorage.getItem('angela_session_id');
        if (!sessionId) {
            sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem('angela_session_id', sessionId);
        }
        return sessionId;
    }
}

// Export for use in renderer
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AngelaAPIClient;
}
