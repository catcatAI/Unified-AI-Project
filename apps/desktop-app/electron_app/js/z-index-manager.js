/**
 * Z-Index 管理系統
 * 統一管理應用中所有元素的 z-index，確保層疊順序正確
 */

class ZIndexManager {
    constructor() {
        // z-index 層級定義（從低到高）
        this.levels = {
            // 基礎層
            background: 0,
            canvas: 1,
            base: 10,

            // UI 元素層
            controls: 100,
            status_bar: 150,
            tooltip: 200,

            // 彈窗層
            modal_overlay: 500,
            modal_content: 600,

            // 通知層
            notification: 1000,

            // 調試層
            debug: 9999
        };

        // 動態 z-index 計數器
        this.counters = {
            modal: 600,
            notification: 1000
        };

        // 當前最高 z-index
        this.highestZIndex = 1000;
    }

    /**
     * 獲取指定層級的 z-index
     * @param {string} level - 層級名稱
     * @returns {number} z-index 值
     */
    getZIndex(level) {
        if (level in this.levels) {
            return this.levels[level];
        }
        console.warn(`[ZIndexManager] 未知的層級: ${level}，使用默認值 0`);
        return 0;
    }

    /**
     * 獲取下一個可用的動態 z-index（用於堆疊元素）
     * @param {string} type - 元素類型
     * @returns {number} 下一个 z-index 值
     */
    getNextZIndex(type = 'modal') {
        if (!this.counters[type]) {
            console.warn(`[ZIndexManager] 未知的類型: ${type}，創建新計數器`);
            this.counters[type] = this.levels.base;
        }

        const zIndex = this.counters[type] + 1;
        this.counters[type] = zIndex;

        if (zIndex > this.highestZIndex) {
            this.highestZIndex = zIndex;
        }

        return zIndex;
    }

    /**
     * 設置元素為最頂層
     * @param {HTMLElement} element - 要設置的元素
     * @param {string} type - 元素類型
     * @returns {number} 分配的 z-index 值
     */
    bringToFront(element, type = 'modal') {
        if (!element) {
            console.error('[ZIndexManager] 元素不存在');
            return 0;
        }

        const zIndex = this.getNextZIndex(type);
        element.style.zIndex = zIndex;
        return zIndex;
    }

    /**
     * 重置指定類型的計數器
     * @param {string} type - 元素類型
     */
    resetCounter(type) {
        if (type in this.counters) {
            this.counters[type] = this.levels[type] || this.levels.base;
        }
    }

    /**
     * 重置所有計數器
     */
    resetAllCounters() {
        this.counters = {
            modal: this.levels.modal_content,
            notification: this.levels.notification
        };
        this.highestZIndex = Math.max(...Object.values(this.levels));
    }

    /**
     * 獲取當前最高 z-index
     * @returns {number} 最高 z-index 值
     */
    getHighestZIndex() {
        return this.highestZIndex;
    }

    /**
     * 驗證 z-index 是否有效
     * @param {number} zIndex - 要驗證的 z-index
     * @returns {boolean} 是否有效
     */
    isValidZIndex(zIndex) {
        return typeof zIndex === 'number' && zIndex >= 0 && zIndex <= 2147483647;
    }

    /**
     * 比較兩個元素的 z-index
     * @param {HTMLElement} element1 - 第一個元素
     * @param {HTMLElement} element2 - 第二個元素
     * @returns {number} 1 (element1 在上), -1 (element2 在上), 0 (相同層級)
     */
    compareZIndex(element1, element2) {
        const zIndex1 = parseInt(element1.style.zIndex) || 0;
        const zIndex2 = parseInt(element2.style.zIndex) || 0;

        if (zIndex1 > zIndex2) return 1;
        if (zIndex1 < zIndex2) return -1;
        return 0;
    }

    /**
     * 獲取所有層級定義
     * @returns {object} 層級定義
     */
    getAllLevels() {
        return { ...this.levels };
    }

    /**
     * 自定義層級（謹慎使用）
     * @param {string} level - 層級名稱
     * @param {number} zIndex - z-index 值
     */
    setLevel(level, zIndex) {
        if (!this.isValidZIndex(zIndex)) {
            console.error(`[ZIndexManager] 無效的 z-index: ${zIndex}`);
            return;
        }
        this.levels[level] = zIndex;
    }
}

// 創建全局單例
const zIndexManager = new ZIndexManager();

// 導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ZIndexManager, zIndexManager };
} else {
    window.ZIndexManager = ZIndexManager;
    window.zIndexManager = zIndexManager;
}