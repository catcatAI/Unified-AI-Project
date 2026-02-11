/**
 * Angela AI - Weak Reference Manager
 * 
 * 弱引用管理器 - 使用WeakMap防止组件循环引用导致内存泄漏
 * 
 * 功能：
 * - 使用WeakMap存储组件引用
 * - 自动垃圾回收不再使用的引用
 * - 循环引用检测
 * - 引用计数统计
 * - 内存使用监控
 */

class WeakRefManager {
    constructor() {
        // ============================================================
        // WeakMap存储
        // ============================================================
        this.weakRefs = new WeakMap();
        
        // ============================================================
        // 引用跟踪（用于调试）
        // ============================================================
        this.refTracking = new Map();  // { name: { count, sources[] } }
        
        // ============================================================
        // 循环引用检测
        // ============================================================
        this.circularDeps = new Set();  // 存储检测到的循环引用
        
        // ============================================================
        // 统计
        // ============================================================
        this.stats = {
            totalRefs: 0,
            activeRefs: 0,
            circularDepsDetected: 0,
            gcCount: 0
        };
        
        console.log('[WeakRefManager] Initialized');
    }

    // ================================================================
    // 弱引用存储
    // ================================================================

    /**
     * 创建弱引用
     * @param {string} name - 引用名称
     * @param {object} value - 要存储的对象
     * @param {string} source - 引用来源（用于调试）
     * @returns {WeakRef} - 弱引用对象
     */
    createRef(name, value, source = 'unknown') {
        if (!value || typeof value !== 'object') {
            console.warn(`[WeakRefManager] Cannot create ref for non-object: ${name}`);
            return null;
        }

        // 检查是否已存在
        if (this.weakRefs.has(value)) {
            console.debug(`[WeakRefManager] Ref already exists for: ${name}`);
            this._trackRef(name, source);
            return this.weakRefs.get(value);
        }

        // 创建弱引用
        const weakRef = new WeakRef(value);
        this.weakRefs.set(value, { name, ref: weakRef, source });
        this.stats.totalRefs++;
        this.stats.activeRefs++;

        // 跟踪引用
        this._trackRef(name, source);

        console.log(`[WeakRefManager] Created ref: ${name} from ${source}`);
        return weakRef;
    }

    /**
     * 获取引用的对象
     * @param {WeakRef} weakRef - 弱引用对象
     * @returns {object|null} - 引用的对象或null（已被GC）
     */
    getRef(weakRef) {
        if (!weakRef || typeof weakRef.deref !== 'function') {
            return null;
        }

        const value = weakRef.deref();
        
        if (value === undefined) {
            this.stats.activeRefs--;
            return null;
        }

        return value;
    }

    /**
     * 通过名称查找引用
     * @param {string} name - 引用名称
     * @returns {object|null} - 引用的对象或null
     */
    findRef(name) {
        // 遍历WeakMap查找
        for (const [value, data] of this.weakRefs.entries()) {
            if (data.name === name) {
                return this.getRef(data.ref);
            }
        }
        return null;
    }

    // ================================================================
    // 引用跟踪
    // ================================================================

    _trackRef(name, source) {
        if (!this.refTracking.has(name)) {
            this.refTracking.set(name, { count: 0, sources: [] });
        }

        const tracking = this.refTracking.get(name);
        tracking.count++;
        
        if (!tracking.sources.includes(source)) {
            tracking.sources.push(source);
        }
    }

    /**
     * 获取引用统计
     * @param {string} name - 引用名称
     * @returns {object|null} - 引用统计或null
     */
    getRefStats(name) {
        return this.refTracking.get(name) || null;
    }

    /**
     * 获取所有引用统计
     * @returns {object} - 所有引用统计
     */
    getAllRefStats() {
        const stats = {};
        for (const [name, tracking] of this.refTracking.entries()) {
            stats[name] = {
                count: tracking.count,
                sources: tracking.sources
            };
        }
        return stats;
    }

    // ================================================================
    // 循环引用检测
    // ================================================================

    /**
     * 检测循环引用
     * @param {object} root - 根对象
     * @param {number} maxDepth - 最大检测深度
     * @returns {array} - 检测到的循环引用路径
     */
    detectCircularDeps(root, maxDepth = 10) {
        const visited = new Set();
        const path = [];
        const circularPaths = [];

        const traverse = (obj, depth) => {
            if (depth > maxDepth) return;
            if (!obj || typeof obj !== 'object') return;
            
            const objId = this._getObjectId(obj);
            
            if (visited.has(objId)) {
                // 检测到循环引用
                const cyclePath = [...path, objId];
                this.circularDeps.add(cyclePath.join(' -> '));
                circularPaths.push(cyclePath);
                this.stats.circularDepsDetected++;
                return;
            }

            visited.add(objId);
            path.push(objId);

            // 遍历属性
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    traverse(obj[key], depth + 1);
                }
            }

            path.pop();
        };

        traverse(root, 0);
        return circularPaths;
    }

    /**
     * 获取检测到的循环引用
     * @returns {array} - 循环引用列表
     */
    getCircularDeps() {
        return Array.from(this.circularDeps);
    }

    /**
     * 清除循环引用记录
     */
    clearCircularDeps() {
        this.circularDeps.clear();
        console.log('[WeakRefManager] Circular deps cleared');
    }

    // ================================================================
    // 内存监控
    // ================================================================

    /**
     * 触发垃圾回收
     * @returns {Promise<number>} - 回收前后的活跃引用数差
     */
    async triggerGC() {
        const beforeCount = this.stats.activeRefs;

        // 尝试触发GC（浏览器环境）
        if (typeof window !== 'undefined' && window.gc) {
            window.gc();
        }

        // 等待一段时间让GC完成
        await new Promise(resolve => setTimeout(resolve, 100));

        // 统计被回收的引用
        const afterCount = this.stats.activeRefs;
        const reclaimed = beforeCount - afterCount;
        this.stats.gcCount++;

        console.log(`[WeakRefManager] GC: ${reclaimed} refs reclaimed`);
        return reclaimed;
    }

    /**
     * 获取统计信息
     * @returns {object} - 统计信息
     */
    getStats() {
        return {
            ...this.stats,
            circularDeps: this.getCircularDeps(),
            refTracking: this.getAllRefStats()
        };
    }

    // ================================================================
    // 工具方法
    // ================================================================

    _getObjectId(obj) {
        // 使用WeakMap的唯一键作为ID
        if (this.weakRefs.has(obj)) {
            return this.weakRefs.get(obj).name;
        }
        // 使用对象自身作为ID（简单实现）
        return obj.toString();
    }

    // ================================================================
    // 清理
    // ================================================================

    /**
     * 清理所有引用
     */
    clear() {
        this.weakRefs = new WeakMap();
        this.refTracking.clear();
        this.circularDeps.clear();
        this.stats = {
            totalRefs: 0,
            activeRefs: 0,
            circularDepsDetected: 0,
            gcCount: 0
        };
        console.log('[WeakRefManager] All refs cleared');
    }

    /**
     * 销毁管理器
     */
    destroy() {
        this.clear();
        console.log('[WeakRefManager] Destroyed');
    }
}

// ================================================================
// 便捷函数 - 组件引用管理
// ================================================================

/**
 * 创建组件引用管理器
 * 帮助管理组件间的引用，防止循环引用
 */
class ComponentRefManager {
    constructor() {
        this.weakRefManager = new WeakRefManager();
        this.componentRefs = new Map();  // { componentName: WeakRef }
    }

    /**
     * 注册组件
     * @param {string} name - 组件名称
     * @param {object} instance - 组件实例
     */
    registerComponent(name, instance) {
        const weakRef = this.weakRefManager.createRef(name, instance, 'component-registration');
        if (weakRef) {
            this.componentRefs.set(name, weakRef);
        }
    }

    /**
     * 获取组件实例
     * @param {string} name - 组件名称
     * @returns {object|null} - 组件实例或null
     */
    getComponent(name) {
        const weakRef = this.componentRefs.get(name);
        if (!weakRef) {
            return null;
        }
        return this.weakRefManager.getRef(weakRef);
    }

    /**
     * 建立组件间引用（使用WeakMap避免循环引用）
     * @param {string} fromName - 源组件名称
     * @param {string} toName - 目标组件名称
     */
    linkComponents(fromName, toName) {
        const fromInstance = this.getComponent(fromName);
        const toInstance = this.getComponent(toName);

        if (!fromInstance || !toInstance) {
            console.warn(`[ComponentRefManager] Cannot link: missing components`);
            return false;
        }

        // 检测循环引用
        const circularDeps = this.weakRefManager.detectCircularDeps(fromInstance);
        if (circularDeps.length > 0) {
            console.warn(`[ComponentRefManager] Circular dependency detected:`, circularDeps);
            return false;
        }

        // 创建弱引用存储
        if (!fromInstance._weakRefs) {
            fromInstance._weakRefs = new Map();
        }

        fromInstance._weakRefs.set(toName, this.componentRefs.get(toName));

        console.log(`[ComponentRefManager] Linked: ${fromName} -> ${toName}`);
        return true;
    }

    /**
     * 断开组件链接
     * @param {string} fromName - 源组件名称
     * @param {string} toName - 目标组件名称（可选，不提供则断开所有）
     */
    unlinkComponents(fromName, toName = null) {
        const fromInstance = this.getComponent(fromName);
        if (!fromInstance || !fromInstance._weakRefs) {
            return;
        }

        if (toName) {
            fromInstance._weakRefs.delete(toName);
            console.log(`[ComponentRefManager] Unlinked: ${fromName} -> ${toName}`);
        } else {
            fromInstance._weakRefs.clear();
            console.log(`[ComponentRefManager] Unlinked all from: ${fromName}`);
        }
    }

    /**
     * 获取组件统计
     * @returns {object} - 组件统计信息
     */
    getComponentStats() {
        const stats = {
            totalComponents: this.componentRefs.size,
            activeComponents: 0,
            components: {}
        };

        for (const [name, weakRef] of this.componentRefs.entries()) {
            const instance = this.weakRefManager.getRef(weakRef);
            if (instance) {
                stats.activeComponents++;
                stats.components[name] = { active: true };
            } else {
                stats.components[name] = { active: false };
            }
        }

        return stats;
    }

    /**
     * 获取引用管理器
     * @returns {WeakRefManager} - 弱引用管理器
     */
    getWeakRefManager() {
        return this.weakRefManager;
    }

    /**
     * 销毁管理器
     */
    destroy() {
        this.weakRefManager.destroy();
        this.componentRefs.clear();
        console.log('[ComponentRefManager] Destroyed');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        WeakRefManager,
        ComponentRefManager
    };
}