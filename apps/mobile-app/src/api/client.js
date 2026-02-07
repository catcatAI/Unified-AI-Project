/**
 * Angela Mobile - API Client
 * Handles communication with Angela backend
 */

import axios from 'axios';
import SecurityManager from './encryption';

class APIClient {
  constructor() {
    this.baseURL = 'http://127.0.0.1:8000';
    this.security = new SecurityManager();
    this.isInitialized = false;
  }

  /**
   * Initialize API client with security
   * @param {string} serverAddress - Backend server address
   * @param {string} keyB - Security key B
   */
  async initialize(serverAddress, keyB) {
    try {
      this.baseURL = `http://${serverAddress}`;
      this.security.init(keyB);
      this.isInitialized = true;
      
      // Test connection
      await this.healthCheck();
      console.log('API Client initialized successfully');
    } catch (error) {
      console.error('Failed to initialize API Client:', error);
      throw error;
    }
  }

  /**
   * Check if client is ready
   * @returns {boolean}
   */
  isReady() {
    return this.isInitialized && this.security.isReady();
  }

  /**
   * Health check endpoint
   * @returns {Promise<object>}
   */
  async healthCheck() {
    const response = await axios.get(`${this.baseURL}/api/v1/health`);
    return response.data;
  }

  /**
   * Get system status (requires signature)
   * @param {object} data - Request data
   * @returns {Promise<object>}
   */
  async getSystemStatus(data = {}) {
    const payload = {
      timestamp: Date.now(),
      ...data
    };

    const encrypted = this.security.encrypt(payload);
    const signature = this.security.generateSignature(payload);

    const response = await axios.post(
      `${this.baseURL}/api/v1/system/status`,
      encrypted,
      {
        headers: {
          'X-Angela-Signature': signature,
          'Content-Type': 'text/plain',
        },
      }
    );

    return this.security.decrypt(response.data);
  }

  /**
   * Send secure test message
   * @param {object} message - Message to send
   * @returns {Promise<object>}
   */
  async sendTestMessage(message) {
    const payload = {
      type: 'test',
      message: message,
      timestamp: Date.now(),
    };

    const encrypted = this.security.encrypt(payload);
    const signature = this.security.generateSignature(payload);

    const response = await axios.post(
      `${this.baseURL}/api/v1/mobile/test`,
      encrypted,
      {
        headers: {
          'X-Angela-Signature': signature,
          'Content-Type': 'text/plain',
        },
      }
    );

    return this.security.decrypt(response.data);
  }

  /**
   * Get sync key C
   * @returns {Promise<object>}
   */
  async getSyncKey() {
    const response = await axios.get(`${this.baseURL}/api/v1/security/sync-key-c`);
    return response.data;
  }

  /**
   * WebSocket connection for real-time updates
   * @param {function} onMessage - Message handler
   * @returns {WebSocket}
   */
  connectWebSocket(onMessage) {
    const ws = new WebSocket(`ws://${this.baseURL.replace('http://', 'ws://')}/ws`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return ws;
  }
}

export default new APIClient();