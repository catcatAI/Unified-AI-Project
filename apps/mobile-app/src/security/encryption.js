import CryptoJS from 'crypto-js';

/**
 * Angela AI Mobile Security Module
 * 負責處理 Key B 加密通訊
 */
class MobileSecurityManager {
  constructor() {
    this.keyB = null; // 從安全存儲中讀取
  }

  /**
   * 初始化密鑰
   * @param {string} keyB - 從後端或安全分發渠道獲取的 Key B
   */
  init(keyB) {
    this.keyB = keyB;
    console.log('✅ Mobile Security initialized with Key B');
  }

  /**
   * 為請求生成簽名
   * @param {string} payload - 請求體內容
   * @returns {string} HMAC-SHA256 簽名
   */
  generateSignature(payload) {
    if (!this.keyB) {
      throw new Error('Security not initialized. Key B missing.');
    }
    return CryptoJS.HmacSHA256(payload, this.keyB).toString();
  }

  /**
   * 封裝安全請求
   * @param {string} url - API URL
   * @param {object} data - 請求數據
   */
  async securePost(url, data) {
    const payload = JSON.stringify(data);
    const signature = this.generateSignature(payload);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Angela-Signature': signature,
      },
      body: payload,
    });

    return response.json();
  }
}

export default new MobileSecurityManager();
