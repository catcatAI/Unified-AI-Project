/**
 * Angela Mobile Security Module
 * Handles AES-256-CBC encryption/decryption using Key B
 */

import CryptoJS from 'crypto-js';

class SecurityManager {
  constructor() {
    this.keyB = null;
    this.isInitialized = false;
  }

  /**
   * Initialize security with Key B
   * @param {string} keyB - The encryption key (minimum 16 characters)
   */
  init(keyB) {
    if (!keyB || keyB.length < 16) {
      throw new Error('Key B must be at least 16 characters');
    }
    this.keyB = keyB;
    this.isInitialized = true;
    console.log('Security Manager initialized');
  }

  /**
   * Check if security is initialized
   * @returns {boolean}
   */
  isReady() {
    return this.isInitialized && this.keyB !== null;
  }

  /**
   * Generate HMAC-SHA256 signature for data
   * @param {object|string} data - Data to sign
   * @returns {string} - Hex signature
   */
  generateSignature(data) {
    if (!this.isReady()) {
      throw new Error('Security not initialized. Call init() first.');
    }

    try {
      const jsonString = typeof data === 'string' ? data : JSON.stringify(data);
      const signature = CryptoJS.HmacSHA256(jsonString, this.keyB).toString(CryptoJS.enc.Hex);
      return signature;
    } catch (error) {
      console.error('Signature generation error:', error);
      throw error;
    }
  }

  /**
   * Encrypt data using AES-256-CBC
   * @param {object|string} data - Data to encrypt
   * @returns {string} - Base64 encoded encrypted data
   */
  encrypt(data) {
    if (!this.isReady()) {
      throw new Error('Security not initialized. Call init() first.');
    }

    try {
      const jsonString = typeof data === 'string' ? data : JSON.stringify(data);
      const encrypted = CryptoJS.AES.encrypt(jsonString, this.keyB).toString();
      return encrypted;
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt data');
    }
  }

  /**
   * Decrypt data using AES-256-CBC
   * @param {string} encryptedData - Base64 encoded encrypted data
   * @returns {object|string} - Decrypted data
   */
  decrypt(encryptedData) {
    if (!this.isReady()) {
      throw new Error('Security not initialized. Call init() first.');
    }

    try {
      const decrypted = CryptoJS.AES.decrypt(encryptedData, this.keyB);
      const decryptedString = decrypted.toString(CryptoJS.enc.Utf8);
      
      if (!decryptedString) {
        throw new Error('Decryption failed - invalid key or corrupted data');
      }

      // Try to parse as JSON, otherwise return as string
      try {
        return JSON.parse(decryptedString);
      } catch {
        return decryptedString;
      }
    } catch (error) {
      console.error('Decryption error:', error);
      throw new Error('Failed to decrypt data');
    }
  }

  /**
   * Send encrypted POST request to backend
   * @param {string} url - Backend endpoint URL
   * @param {object} data - Data to send
   * @returns {Promise<object>} - Decrypted response data
   */
  async securePost(url, data) {
    if (!this.isReady()) {
      throw new Error('Security not initialized. Call init() first.');
    }

    try {
      // Encrypt the request payload
      const encryptedPayload = this.encrypt(data);

      // Send encrypted request
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Encrypted': 'true'
        },
        body: JSON.stringify({
          encrypted: encryptedPayload
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const responseData = await response.json();

      // Decrypt the response if it's encrypted
      if (responseData.encrypted) {
        return this.decrypt(responseData.encrypted);
      }

      return responseData;
    } catch (error) {
      console.error('Secure POST error:', error);
      throw error;
    }
  }

  /**
   * Send encrypted GET request to backend
   * @param {string} url - Backend endpoint URL
   * @returns {Promise<object>} - Decrypted response data
   */
  async secureGet(url) {
    if (!this.isReady()) {
      throw new Error('Security not initialized. Call init() first.');
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Encrypted': 'true'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const responseData = await response.json();

      // Decrypt the response if it's encrypted
      if (responseData.encrypted) {
        return this.decrypt(responseData.encrypted);
      }

      return responseData;
    } catch (error) {
      console.error('Secure GET error:', error);
      throw error;
    }
  }

  /**
   * Generate a secure random key
   * @param {number} length - Key length (default: 32)
   * @returns {string} - Random key
   */
  static generateKey(length = 32) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let key = '';
    for (let i = 0; i < length; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return key;
  }

  /**
   * Clear security credentials
   */
  clear() {
    this.keyB = null;
    this.isInitialized = false;
    console.log('Security Manager cleared');
  }
}

// Export singleton instance
const security = new SecurityManager();
export default security;
