/**
 * Angela AI - Time Evolution Manager
 * 
 * 时间演化管理器 - 增强Angela的时间感知和状态演化能力
 * 
 * 功能：
 * - 状态时间衰减（情绪随时间自然衰减）
 * - 时间段感知（白天/夜晚/晨昏）
 * - 节奏感知（工作/休息/娱乐时段）
 * - 事件时间线跟踪
 * - 未来事件预测
 * - 时间相关行为模式
 */

class TimeEvolutionManager {
    constructor(config = {}) {
        // ============================================================
        // 配置
        // ============================================================
        this.config = {
            // 时间衰减配置
            decay: {
                energy: config.decay?.energy || 0.01,      // 能量衰减率
                comfort: config.decay?.comfort || 0.005,    // 舒适度衰减率
                arousal: config.decay?.arousal || 0.02,     // 唤醒度衰减率
                vitality: config.decay?.vitality || 0.015,  // 活力衰减率
                curiosity: config.decay?.curiosity || 0.03, // 好奇心衰减率
                focus: config.decay?.focus || 0.025,       // 专注度衰减率
                happiness: config.decay?.happiness || 0.02, // 快乐衰减率
                calm: config.decay?.calm || 0.01,          // 平静衰减率
                love: config.decay?.love || 0.005,         // 爱意衰减率
                trust: config.decay?.trust || 0.003,       // 信任衰减率
                attention: config.decay?.attention || 0.05, // 注意力衰减率
                bond: config.decay?.bond || 0.002,         // 纽带衰减率
                intimacy: config.decay?.intimacy || 0.001, // 亲密度衰减率
                engagement: config.decay?.engagement || 0.04 // 参与度衰减率
            },
            
            // 时间段配置
            timeSegments: {
                dawn: { start: 5, end: 8, name: '黎明', mood: 'peaceful' },
                morning: { start: 8, end: 12, name: '上午', mood: 'energetic' },
                noon: { start: 12, end: 14, name: '中午', mood: 'relaxed' },
                afternoon: { start: 14, end: 18, name: '下午', mood: 'productive' },
                evening: { start: 18, end: 21, name: '傍晚', mood: 'social' },
                night: { start: 21, end: 24, name: '夜晚', mood: 'calm' },
                midnight: { start: 0, end: 5, name: '深夜', mood: 'sleepy' }
            },
            
            // 节奏感知配置
            rhythms: {
                work: { start: 9, end: 18, name: '工作时间', activity: 'high' },
                rest: { start: 18, end: 22, name: '休息时间', activity: 'medium' },
                sleep: { start: 22, end: 7, name: '睡眠时间', activity: 'low' }
            },
            
            // 更新间隔
            updateInterval: config.updateInterval || 1000,  // 1秒更新一次
            decayInterval: config.decayInterval || 5000     // 5秒衰减一次
        };

        // ============================================================
        // 当前状态
        // ============================================================
        this.currentTime = Date.now();
        this.currentSegment = null;
        this.currentRhythm = null;
        this.lastDecayTime = Date.now();

        // ============================================================
        // 时间线
        // ============================================================
        this.timeline = [];  // 事件时间线
        this.futureEvents = [];  // 未来事件

        // ============================================================
        // 定时器
        // ============================================================
        this.updateTimer = null;
        this.decayTimer = null;

        // ============================================================
        // 行为模式
        // ============================================================
        this.behaviorPatterns = {
            dawn: { activities: ['waking', 'stretching', 'morning_routine'] },
            morning: { activities: ['working', 'learning', 'exercising'] },
            noon: { activities: ['eating', 'relaxing', 'chatting'] },
            afternoon: { activities: ['working', 'learning', 'creating'] },
            evening: { activities: ['socializing', 'gaming', 'watching'] },
            night: { activities: ['reading', 'thinking', 'preparing_sleep'] },
            midnight: { activities: ['sleeping', 'dreaming', 'resting'] }
        };

        // ============================================================
        // 统计
        // ============================================================
        this.stats = {
            totalDecays: 0,
            totalUpdates: 0,
            eventsLogged: 0
        };

        console.log('[TimeEvolutionManager] Initialized');
    }

    // ================================================================
    // 初始化和启动
    // ================================================================

    start() {
        console.log('[TimeEvolutionManager] Starting...');
        
        // 启动更新定时器
        this.updateTimer = setInterval(() => {
            this.update();
        }, this.config.updateInterval);
        
        // 启动衰减定时器
        this.decayTimer = setInterval(() => {
            this.applyDecay();
        }, this.config.decayInterval);
        
        // 初始更新
        this.update();
        
        console.log('[TimeEvolutionManager] Started');
    }

    stop() {
        console.log('[TimeEvolutionManager] Stopping...');
        
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
        
        if (this.decayTimer) {
            clearInterval(this.decayTimer);
            this.decayTimer = null;
        }
        
        console.log('[TimeEvolutionManager] Stopped');
    }

    // ================================================================
    // 时间更新
    // ================================================================

    update() {
        this.currentTime = Date.now();
        
        // 更新时间段
        this.currentSegment = this._detectTimeSegment();
        
        // 更新节奏
        this.currentRhythm = this._detectRhythm();
        
        this.stats.totalUpdates++;
    }

    /**
     * 检测当前时间段
     */
    _detectTimeSegment() {
        const hour = new Date(this.currentTime).getHours();
        
        for (const [name, segment] of Object.entries(this.config.timeSegments)) {
            if (segment.start <= hour && hour < segment.end) {
                return { name, ...segment };
            }
        }
        
        // 默认返回深夜
        return this.config.timeSegments.midnight;
    }

    /**
     * 检测当前节奏
     */
    _detectRhythm() {
        const hour = new Date(this.currentTime).getHours();
        
        for (const [name, rhythm] of Object.entries(this.config.rhythms)) {
            const start = rhythm.start;
            const end = rhythm.end;
            
            // 处理跨天情况（如睡眠时间22:00-7:00）
            if (start < end) {
                if (start <= hour && hour < end) {
                    return { name, ...rhythm };
                }
            } else {
                if (hour >= start || hour < end) {
                    return { name, ...rhythm };
                }
            }
        }
        
        return this.config.rhythms.work;
    }

    // ================================================================
    // 状态衰减
    // ================================================================

    /**
     * 应用时间衰减到状态
     * @param {object} state - 状态对象 {alpha, beta, gamma, delta}
     * @returns {object} - 衰减后的状态
     */
    applyDecay(state) {
        if (!state) {
            console.warn('[TimeEvolutionManager] No state to apply decay');
            return null;
        }

        const decayed = { ...state };
        const now = Date.now();
        const deltaTime = (now - this.lastDecayTime) / 1000;  // 转换为秒

        this.lastDecayTime = now;

        // Alpha维度衰减
        if (decayed.alpha) {
            decayed.alpha.energy = Math.max(0, decayed.alpha.energy - this.config.decay.energy * deltaTime);
            decayed.alpha.comfort = Math.max(0, decayed.alpha.comfort - this.config.decay.comfort * deltaTime);
            decayed.alpha.arousal = Math.max(0, decayed.alpha.arousal - this.config.decay.arousal * deltaTime);
            decayed.alpha.vitality = Math.max(0, decayed.alpha.vitality - this.config.decay.vitality * deltaTime);
        }

        // Beta维度衰减
        if (decayed.beta) {
            decayed.beta.curiosity = Math.max(0, decayed.beta.curiosity - this.config.decay.curiosity * deltaTime);
            decayed.beta.focus = Math.max(0, decayed.beta.focus - this.config.decay.focus * deltaTime);
            decayed.beta.clarity = Math.max(0, decayed.beta.clarity - this.config.decay.focus * deltaTime * 0.5);
            decayed.beta.creativity = Math.max(0, decayed.beta.creativity - this.config.decay.curiosity * deltaTime * 0.7);
        }

        // Gamma维度衰减
        if (decayed.gamma) {
            decayed.gamma.happiness = Math.max(0, decayed.gamma.happiness - this.config.decay.happiness * deltaTime);
            decayed.gamma.calm = Math.max(0, decayed.gamma.calm - this.config.decay.calm * deltaTime);
            decayed.gamma.love = Math.max(0, decayed.gamma.love - this.config.decay.love * deltaTime);
            decayed.gamma.trust = Math.max(0, decayed.gamma.trust - this.config.decay.trust * deltaTime);
        }

        // Delta维度衰减
        if (decayed.delta) {
            decayed.delta.attention = Math.max(0, decayed.delta.attention - this.config.decay.attention * deltaTime);
            decayed.delta.bond = Math.max(0, decayed.delta.bond - this.config.decay.bond * deltaTime);
            decayed.delta.intimacy = Math.max(0, decayed.delta.intimacy - this.config.decay.intimacy * deltaTime);
            decayed.delta.engagement = Math.max(0, decayed.delta.engagement - this.config.decay.engagement * deltaTime);
        }

        this.stats.totalDecays++;
        return decayed;
    }

    // ================================================================
    // 事件时间线
    // ================================================================

    /**
     * 记录事件
     * @param {string} type - 事件类型
     * @param {object} data - 事件数据
     */
    logEvent(type, data = {}) {
        const event = {
            type,
            data,
            timestamp: this.currentTime,
            segment: this.currentSegment?.name,
            rhythm: this.currentRhythm?.name
        };

        this.timeline.push(event);
        this.stats.eventsLogged++;

        // 限制时间线长度
        if (this.timeline.length > 1000) {
            this.timeline.shift();
        }

        console.log(`[TimeEvolutionManager] Event logged: ${type}`, event);
    }

    /**
     * 获取时间线
     * @param {number} limit - 限制条数
     * @returns {array} - 事件列表
     */
    getTimeline(limit = 100) {
        return this.timeline.slice(-limit);
    }

    /**
     * 清空时间线
     */
    clearTimeline() {
        this.timeline = [];
        console.log('[TimeEvolutionManager] Timeline cleared');
    }

    // ================================================================
    // 未来事件
    // ================================================================

    /**
     * 添加未来事件
     * @param {string} type - 事件类型
     * @param {number} delay - 延迟时间（毫秒）
     * @param {object} data - 事件数据
     */
    addFutureEvent(type, delay, data = {}) {
        const event = {
            type,
            data,
            scheduledTime: this.currentTime + delay,
            completed: false
        };

        this.futureEvents.push(event);
        console.log(`[TimeEvolutionManager] Future event added: ${type} at ${new Date(event.scheduledTime).toLocaleString()}`);
    }

    /**
     * 检查并触发到期的未来事件
     * @returns {array} - 到期的事件列表
     */
    checkFutureEvents() {
        const now = this.currentTime;
        const dueEvents = [];

        for (const event of this.futureEvents) {
            if (!event.completed && event.scheduledTime <= now) {
                event.completed = true;
                dueEvents.push(event);
            }
        }

        // 清理已完成的事件
        this.futureEvents = this.futureEvents.filter(e => !e.completed);

        return dueEvents;
    }

    // ================================================================
    // 行为模式
    // ================================================================

    /**
     * 获取当前行为模式
     * @returns {object} - 行为模式
     */
    getBehaviorPattern() {
        if (!this.currentSegment) {
            return null;
        }

        return this.behaviorPatterns[this.currentSegment.name] || null;
    }

    /**
     * 获取推荐活动
     * @returns {array} - 推荐活动列表
     */
    getRecommendedActivities() {
        const pattern = this.getBehaviorPattern();
        return pattern ? pattern.activities : [];
    }

    // ================================================================
    // 时间感知
    // ================================================================

    /**
     * 获取当前时间段信息
     * @returns {object} - 时间段信息
     */
    getTimeSegment() {
        return this.currentSegment;
    }

    /**
     * 获取当前节奏信息
     * @returns {object} - 节奏信息
     */
    getRhythm() {
        return this.currentRhythm;
    }

    /**
     * 获取时间感知状态
     * @returns {object} - 完整的时间感知状态
     */
    getTimeAwareness() {
        return {
            currentTime: this.currentTime,
            formattedTime: new Date(this.currentTime).toLocaleString(),
            timeSegment: this.currentSegment,
            rhythm: this.currentRhythm,
            behaviorPattern: this.getBehaviorPattern(),
            recommendedActivities: this.getRecommendedActivities()
        };
    }

    // ================================================================
    // 统计和配置
    // ================================================================

    getStats() {
        return {
            ...this.stats,
            timelineLength: this.timeline.length,
            futureEventsCount: this.futureEvents.length,
            currentTime: this.currentTime
        };
    }

    getConfig() {
        return JSON.parse(JSON.stringify(this.config));
    }

    setDecayRate(dimension, rate) {
        if (this.config.decay[dimension] !== undefined) {
            this.config.decay[dimension] = rate;
            console.log(`[TimeEvolutionManager] Decay rate updated: ${dimension} = ${rate}`);
        }
    }

    // ================================================================
    // 销毁
    // ================================================================

    destroy() {
        this.stop();
        this.timeline = [];
        this.futureEvents = [];
        console.log('[TimeEvolutionManager] Destroyed');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TimeEvolutionManager;
}