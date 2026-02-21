/**
 * Angela AI Desktop Security Manager
 * 負責處理 Key C 跨端同步與本地加密
 */
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const http = require('http');

class SecurityManager {
    constructor() {
        this.keyC = null;
        this.keyPath = null;
    }

    /**
     * 初始化密鑰管理器，載入本地存儲或從後端同步
     * @param {string} userDataPath - Electron 的 userData 目錄
     * @param {string} backendIP - 後端 IP 地址
     */
    async setup(userDataPath, backendIP = '127.0.0.1') {
        this.keyPath = path.join(userDataPath, 'security_key_c.dat');
        
        // 1. 嘗試從本地文件載入
        if (fs.existsSync(this.keyPath)) {
            try {
                this.keyC = fs.readFileSync(this.keyPath, 'utf8').trim();
                console.log('🔐 Loaded Key C from local storage');
            } catch (e) {
                console.error('Failed to read stored Key C:', e);
            }
        }

        // 2. 如果本地沒有，則從後端同步
        if (!this.keyC) {
            await this.syncFromBackend(backendIP);
        }

        return this.keyC !== null;
    }

    /**
     * 從後端獲取 Key C
     */
    syncFromBackend(backendIP) {
        return new Promise((resolve) => {
            console.log(`🔄 Syncing Key C from backend: ${backendIP}...`);
            const options = {
                hostname: backendIP,
                port: 8000,
                path: '/api/v1/security/sync-key-c',
                method: 'GET',
                timeout: 5000
            };

            const req = http.get(options, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const json = JSON.parse(data);
                        if (json.key_c) {
                            this.keyC = json.key_c;
                            this.saveKeyLocally();
                            console.log('✅ Key C synced successfully');
                            resolve(true);
                        } else {
                            resolve(false);
                        }
                    } catch (e) {
                        resolve(false);
                    }
                });
            });

            req.on('error', (e) => {
                console.error('Sync request error:', e.message);
                resolve(false);
            });

            req.on('timeout', () => {
                req.destroy();
                resolve(false);
            });
        });
    }

    /**
     * 將 Key C 保存到本地
     */
    saveKeyLocally() {
        if (this.keyC && this.keyPath) {
            try {
                fs.writeFileSync(this.keyPath, this.keyC, 'utf8');
            } catch (e) {
                console.error('Failed to save Key C:', e);
            }
        }
    }

    /**
     * 手動初始化密鑰
     * @param {string} keyC - 從後端獲取的 Key C
     */
    init(keyC) {
        this.keyC = keyC;
        this.saveKeyLocally();
        console.log('✅ Desktop Security initialized with manual Key C');
    }

    /**
     * 檢查是否已初始化
     */
    isInitialized() {
        return this.keyC !== null;
    }

    /**
     * 獲取當前 Key C (僅限內部使用)
     */
    getKeyC() {
        return this.keyC;
    }

    /**
     * 數據加密 (AES-256-CBC) - 使用隨機鹽增強安全性
     * @param {string} data - 要加密的數據
     * @returns {string} 加密後的數據 (salt:iv:data)
     */
    encrypt(data) {
        if (!this.keyC) throw new Error('Security not initialized');

        // 生成隨機鹽值，增強安全性
        const salt = crypto.randomBytes(32);

        // 衍生密鑰
        const derivedKey = crypto.scryptSync(this.keyC, salt, 32);
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-cbc', derivedKey, iv);

        let encrypted = cipher.update(data, 'utf8', 'base64');
        encrypted += cipher.final('base64');

        // 返回格式: salt:iv:encryptedData
        return salt.toString('base64') + ':' + iv.toString('base64') + ':' + encrypted;
    }

    /**
     * 數據解密
     * @param {string} encryptedData - 加密數據 (salt:iv:data)
     * @returns {string} 解密後的數據
     */
    decrypt(encryptedData) {
        if (!this.keyC) throw new Error('Security not initialized');

        // 解析格式: salt:iv:encryptedData
        const parts = encryptedData.split(':');
        if (parts.length !== 3) {
            throw new Error('Invalid encrypted data format');
        }

        const salt = Buffer.from(parts[0], 'base64');
        const iv = Buffer.from(parts[1], 'base64');
        const dataBase64 = parts[2];

        // 使用相同的鹽值衍生密鑰
        const derivedKey = crypto.scryptSync(this.keyC, salt, 32);
        const decipher = crypto.createDecipheriv('aes-256-cbc', derivedKey, iv);

        let decrypted = decipher.update(dataBase64, 'base64', 'utf8');
        decrypted += decipher.final('utf8');

        return decrypted;
    }
}

module.exports = new SecurityManager();
