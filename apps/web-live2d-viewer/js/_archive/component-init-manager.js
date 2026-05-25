/**
 * Angela AI - Component Initialization Manager
 * 
 * 组件初始化管理器 - 处理组件初始化顺序和依赖关系
 * 
 * 功能：
 * - 基于依赖图的拓扑排序
 * - 初始化状态跟踪
 * - 失败回滚机制
 * - 初始化超时控制
 * - 依赖注入支持
 * - 并行初始化优化
 */

class ComponentInitManager {
    constructor(options = {}) {
        // ============================================================
        // 配置
        // ============================================================
        this.config = {
            timeout: options.timeout || 30000,  // 默认超时30秒
            parallelInit: options.parallelInit !== false,  // 默认启用并行初始化
            rollbackOnError: options.rollbackOnError !== false,  // 默认启用失败回滚
            retryAttempts: options.retryAttempts || 3,  // 默认重试3次
            retryDelay: options.retryDelay || 1000  // 默认重试延迟1秒
        };

        // ============================================================
        // 组件注册表
        // ============================================================
        this.components = new Map();  // { name: { init, deps, state, instance, ... } }

        // ============================================================
        // 初始化状态
        // ============================================================
        this.state = {
            initialized: false,
            initializing: false,
            failed: false,
            startTime: null,
            endTime: null,
            errors: []
        };

        // ============================================================
        // 统计
        // ============================================================
        this.stats = {
            totalComponents: 0,
            initializedComponents: 0,
            failedComponents: 0,
            skippedComponents: 0,
            totalTime: 0
        };

        console.log('[ComponentInitManager] Initialized');
    }

    // ================================================================
    // 组件注册
    // ================================================================

    /**
     * 注册组件
     * @param {string} name - 组件名称
     * @param {object} config - 组件配置
     * @returns {ComponentInitManager} - 链式调用
     */
    register(name, config) {
        this.components.set(name, {
            name: name,
            init: config.init || null,
            deps: config.deps || [],  // 依赖的组件名称
            optional: config.optional || false,  // 是否为可选组件
            priority: config.priority || 0,  // 优先级（数字越大越优先）
            timeout: config.timeout || this.config.timeout,
            retryAttempts: config.retryAttempts || this.config.retryAttempts,
            state: 'pending',  // pending, initializing, initialized, failed, skipped
            instance: null,
            error: null,
            initTime: 0
        });

        this.stats.totalComponents++;
        console.log(`[ComponentInitManager] Registered component: ${name}`);

        return this;
    }

    /**
     * 批量注册组件
     * @param {object} components - 组件配置对象 { name: config, ... }
     * @returns {ComponentInitManager}
     */
    registerAll(components) {
        for (const [name, config] of Object.entries(components)) {
            this.register(name, config);
        }
        return this;
    }

    // ================================================================
    // 初始化执行
    // ================================================================

    /**
     * 执行初始化
     * @returns {Promise<boolean>} - 是否全部成功
     */
    async initialize() {
        if (this.state.initializing) {
            console.warn('[ComponentInitManager] Already initializing');
            return false;
        }

        if (this.state.initialized) {
            console.warn('[ComponentInitManager] Already initialized');
            return true;
        }

        this.state.initializing = true;
        this.state.startTime = Date.now();
        console.log('[ComponentInitManager] Starting initialization...');

        try {
            // 1. 构建依赖图
            const initOrder = this._buildInitOrder();
            console.log('[ComponentInitManager] Init order:', initOrder.map(c => c.name));

            // 2. 按顺序初始化
            for (const component of initOrder) {
                await this._initializeComponent(component);
            }

            // 3. 检查状态
            const allInitialized = this._checkAllInitialized();

            if (allInitialized) {
                this.state.initialized = true;
                this.state.endTime = Date.now();
                this.state.initializing = false;
                this.stats.totalTime = this.state.endTime - this.state.startTime;
                console.log('[ComponentInitManager] Initialization complete', this.stats);
            } else {
                this.state.failed = true;
                this.state.initializing = false;
                console.error('[ComponentInitManager] Initialization failed', this.stats);
                
                // 回滚
                if (this.config.rollbackOnError) {
                    await this._rollback();
                }
            }

            return allInitialized;

        } catch (error) {
            console.error('[ComponentInitManager] Critical error:', error);
            this.state.failed = true;
            this.state.initializing = false;
            this.state.errors.push(error);

            // 回滚
            if (this.config.rollbackOnError) {
                await this._rollback();
            }

            return false;
        }
    }

    /**
     * 初始化单个组件
     */
    async _initializeComponent(component) {
        if (component.state === 'initialized') {
            console.log(`[ComponentInitManager] ${component.name} already initialized`);
            return true;
        }

        // 检查依赖
        const missingDeps = this._checkDependencies(component);
        if (missingDeps.length > 0) {
            if (component.optional) {
                component.state = 'skipped';
                component.error = new Error(`Missing dependencies: ${missingDeps.join(', ')}`);
                this.stats.skippedComponents++;
                console.warn(`[ComponentInitManager] ${component.name} skipped (missing deps: ${missingDeps.join(', ')})`);
                return true;  // 可选组件跳过不算失败
            } else {
                component.state = 'failed';
                component.error = new Error(`Missing required dependencies: ${missingDeps.join(', ')}`);
                this.stats.failedComponents++;
                console.error(`[ComponentInitManager] ${component.name} failed (missing deps: ${missingDeps.join(', ')})`);
                return false;
            }
        }

        component.state = 'initializing';
        const startTime = Date.now();

        for (let attempt = 1; attempt <= component.retryAttempts; attempt++) {
            try {
                // 获取依赖实例
                const depInstances = this._getDependencyInstances(component);

                // 调用初始化函数
                if (typeof component.init === 'function') {
                    const instance = await Promise.race([
                        component.init(depInstances),
                        this._timeoutPromise(component.timeout)
                    ]);

                    component.instance = instance;
                    component.state = 'initialized';
                    component.initTime = Date.now() - startTime;
                    this.stats.initializedComponents++;

                    console.log(`[ComponentInitManager] ${component.name} initialized (${component.initTime}ms)`);
                    return true;
                } else {
                    console.warn(`[ComponentInitManager] ${component.name} has no init function`);
                    component.state = 'initialized';
                    return true;
                }

            } catch (error) {
                if (attempt < component.retryAttempts) {
                    console.warn(`[ComponentInitManager] ${component.name} init attempt ${attempt} failed: ${error}`);
                    await this._sleep(this.config.retryDelay * attempt);  // 指数退避
                } else {
                    component.state = 'failed';
                    component.error = error;
                    this.stats.failedComponents++;
                    this.state.errors.push(error);

                    if (component.optional) {
                        console.warn(`[ComponentInitManager] ${component.name} failed (optional): ${error}`);
                        return true;  // 可选组件失败不算失败
                    } else {
                        console.error(`[ComponentInitManager] ${component.name} failed: ${error}`);
                        return false;
                    }
                }
            }
        }

        return false;
    }

    // ================================================================
    // 依赖管理
    // ================================================================

    /**
     * 构建初始化顺序（拓扑排序）
     */
    _buildInitOrder() {
        const components = Array.from(this.components.values());
        const order = [];
        const visited = new Set();
        const visiting = new Set();

        // 按优先级排序
        components.sort((a, b) => b.priority - a.priority);

        // DFS拓扑排序
        const visit = (component) => {
            if (visited.has(component.name)) return;
            if (visiting.has(component.name)) {
                throw new Error(`Circular dependency detected: ${component.name}`);
            }

            visiting.add(component.name);

            // 先初始化依赖
            for (const depName of component.deps) {
                const dep = this.components.get(depName);
                if (dep) {
                    visit(dep);
                }
            }

            visiting.delete(component.name);
            visited.add(component.name);
            order.push(component);
        };

        for (const component of components) {
            visit(component);
        }

        return order;
    }

    /**
     * 检查依赖是否都已初始化
     */
    _checkDependencies(component) {
        const missing = [];
        for (const depName of component.deps) {
            const dep = this.components.get(depName);
            if (!dep || dep.state !== 'initialized') {
                missing.push(depName);
            }
        }
        return missing;
    }

    /**
     * 获取依赖实例
     */
    _getDependencyInstances(component) {
        const instances = {};
        for (const depName of component.deps) {
            const dep = this.components.get(depName);
            if (dep && dep.state === 'initialized') {
                instances[depName] = dep.instance;
            }
        }
        return instances;
    }

    /**
     * 检查所有组件是否已初始化
     */
    _checkAllInitialized() {
        for (const component of this.components.values()) {
            if (!component.optional && component.state !== 'initialized' && component.state !== 'skipped') {
                return false;
            }
        }
        return true;
    }

    // ================================================================
    // 回滚机制
    // ================================================================

    async _rollback() {
        console.log('[ComponentInitManager] Rolling back...');
        
        // 按初始化顺序的反序销毁
        const components = Array.from(this.components.values())
            .filter(c => c.state === 'initialized')
            .reverse();

        for (const component of components) {
            try {
                if (component.instance && typeof component.instance.destroy === 'function') {
                    await component.instance.destroy();
                }
                component.state = 'pending';
                component.instance = null;
                console.log(`[ComponentInitManager] Rolled back: ${component.name}`);
            } catch (error) {
                console.error(`[ComponentInitManager] Rollback failed for ${component.name}:`, error);
            }
        }
    }

    // ================================================================
    // 工具方法
    // ================================================================

    _timeoutPromise(ms) {
        return new Promise((_, reject) => {
            setTimeout(() => reject(new Error(`Initialization timeout after ${ms}ms`)), ms);
        });
    }

    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ================================================================
    // 查询方法
    // ================================================================

    /**
     * 获取组件实例
     */
    get(name) {
        const component = this.components.get(name);
        return component ? component.instance : null;
    }

    /**
     * 获取组件状态
     */
    getState(name) {
        const component = this.components.get(name);
        return component ? {
            state: component.state,
            error: component.error,
            initTime: component.initTime
        } : null;
    }

    /**
     * 获取所有组件状态
     */
    getAllStates() {
        const states = {};
        for (const [name, component] of this.components.entries()) {
            states[name] = {
                state: component.state,
                error: component.error,
                initTime: component.initTime
            };
        }
        return states;
    }

    /**
     * 获取统计信息
     */
    getStats() {
        return {
            ...this.stats,
            managerState: {
                initialized: this.state.initialized,
                initializing: this.state.initializing,
                failed: this.state.failed,
                errors: this.state.errors
            }
        };
    }

    // ================================================================
    // 重置
    // ================================================================

    reset() {
        console.log('[ComponentInitManager] Resetting...');
        
        // 销毁所有组件
        this._rollback();

        // 重置状态
        this.state = {
            initialized: false,
            initializing: false,
            failed: false,
            startTime: null,
            endTime: null,
            errors: []
        };

        // 重置统计
        this.stats = {
            totalComponents: this.components.size,
            initializedComponents: 0,
            failedComponents: 0,
            skippedComponents: 0,
            totalTime: 0
        };

        // 重置组件状态
        for (const component of this.components.values()) {
            component.state = 'pending';
            component.instance = null;
            component.error = null;
            component.initTime = 0;
        }
    }

    // ================================================================
    // 销毁
    // ================================================================

    async destroy() {
        console.log('[ComponentInitManager] Destroying...');
        await this._rollback();
        this.components.clear();
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComponentInitManager;
}