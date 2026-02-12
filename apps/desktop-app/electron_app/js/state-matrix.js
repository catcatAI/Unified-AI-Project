/**
 * =============================================================================
 * ANGELA-MATRIX: L1-L6[全层] αβγδ [A/B/C] L2+
 * =============================================================================
 *
 * 职责: 管理 4D 状态矩阵 (αβγδ)，实时更新所有维度
 * 维度: 涉及所有四个维度 (αβγδ)
 *   - α (Alpha): 生理维度 - energy, comfort, arousal, rest_need, vitality, tension
 *   - β (Beta): 认知维度 - curiosity, focus, confusion, learning, clarity, creativity
 *   - γ (Gamma): 物理维度 - happiness, sadness, anger, fear, surprise, disgust
 *   - δ (Delta): 精神维度 - mood, emotion, personality, wisdom, empathy
 * 安全: 跨所有安全层级 (A/B/C)
 * 成熟度: L2+ 等级开始接触状态矩阵概念
 *
 * @class StateMatrix4D
 */

class StateMatrix4D {
    constructor(config = {}) {
        this.config = config;
        
        this.alpha = {
            name: 'alpha',
            cn_name: '生理维度',
            values: {
                energy: 0.5,
                comfort: 0.5,
                arousal: 0.5,
                rest_need: 0.5,
                vitality: 0.5,
                tension: 0.0
            },
            weight: config.alpha_weight || 1.0,
            timestamp: Date.now()
        };
        
        this.beta = {
            name: 'beta',
            cn_name: '认知维度',
            values: {
                curiosity: 0.5,
                focus: 0.5,
                confusion: 0.0,
                learning: 0.5,
                clarity: 0.5,
                creativity: 0.5
            },
            weight: config.beta_weight || 1.0,
            timestamp: Date.now()
        };
        
        this.gamma = {
            name: 'gamma',
            cn_name: '情感维度',
            values: {
                happiness: 0.5,
                sadness: 0.0,
                anger: 0.0,
                fear: 0.0,
                disgust: 0.0,
                surprise: 0.0,
                trust: 0.5,
                anticipation: 0.5,
                love: 0.0,
                calm: 0.5
            },
            weight: config.gamma_weight || 1.0,
            timestamp: Date.now()
        };
        
        this.delta = {
            name: 'delta',
            cn_name: '社交维度',
            values: {
                attention: 0.5,
                bond: 0.5,
                trust: 0.5,
                presence: 0.5,
                intimacy: 0.0,
                engagement: 0.5
            },
            weight: config.delta_weight || 1.0,
            timestamp: Date.now()
        };
        
        this.dimensions = {
            alpha: this.alpha,
            beta: this.beta,
            gamma: this.gamma,
            delta: this.delta
        };
        
        this.influenceMatrix = config.influence_matrix || {
            alpha: { beta: 0.3, gamma: 0.5, delta: 0.2 },
            beta: { alpha: 0.2, gamma: 0.4, delta: 0.3 },
            gamma: { alpha: 0.4, beta: 0.3, delta: 0.5 },
            delta: { alpha: 0.2, beta: 0.3, gamma: 0.6 }
        };
        
        this.history = [];
        this.maxHistory = config.max_history || 1000;
        this.historyTimeWindow = config.history_time_window || 3600000; // 默认1小时（毫秒）
        this.historyMemoryThreshold = config.history_memory_threshold || 10 * 1024 * 1024; // 默认10MB
        this.updateCount = 0;
        this.createdAt = Date.now();
        
        // WebSocket消息节流
        this._messageThrottleInterval = 100; // 100ms节流间隔
        this._lastMessageTime = 0;
        this._pendingMessage = null;
        this._messageTimer = null;
        this.lastUpdate = Date.now();
        this.changeCallbacks = [];
        this.thresholdCallbacks = {};
        this.live2DManager = null;
        this.websocket = null;
        
        // 启动历史清理定时器（每5分钟清理一次）
        this._startHistoryCleanupTimer();
    }
    
    setLive2DManager(manager) {
        this.live2DManager = manager;
    }
    
    setWebSocket(ws) {
        this.websocket = ws;
    }
    
    updateAlpha(kwargs) {
        for (const [key, value] of Object.entries(kwargs)) {
            if (key in this.alpha.values) {
                this.alpha.values[key] = Math.max(0, Math.min(1, parseFloat(value)));
            }
        }
        this.alpha.timestamp = Date.now();
        this.postUpdate('alpha', kwargs);
    }
    
    updateBeta(kwargs) {
        for (const [key, value] of Object.entries(kwargs)) {
            if (key in this.beta.values) {
                this.beta.values[key] = Math.max(0, Math.min(1, parseFloat(value)));
            }
        }
        this.beta.timestamp = Date.now();
        this.postUpdate('beta', kwargs);
    }
    
    updateGamma(kwargs) {
        for (const [key, value] of Object.entries(kwargs)) {
            if (key in this.gamma.values) {
                this.gamma.values[key] = Math.max(0, Math.min(1, parseFloat(value)));
            }
        }
        this.gamma.timestamp = Date.now();
        this.postUpdate('gamma', kwargs);
    }
    
    updateDelta(kwargs) {
        for (const [key, value] of Object.entries(kwargs)) {
            if (key in this.delta.values) {
                this.delta.values[key] = Math.max(0, Math.min(1, parseFloat(value)));
            }
        }
        this.delta.timestamp = Date.now();
        this.postUpdate('delta', kwargs);
    }
    
    postUpdate(dimensionName, changes) {
        this.updateCount++;
        this.lastUpdate = Date.now();
        
        this.recordHistory();
        
        const dimState = this.dimensions[dimensionName];
        this.changeCallbacks.forEach(callback => {
            try {
                callback(dimensionName, { ...dimState.values });
            } catch (e) {
                console.error('StateMatrix callback error:', e);
            }
        });
        
        this.checkThresholds(dimensionName);
        
        this.applyLive2DChanges(dimensionName, changes);
        
        if (this.websocket && this.websocket.isConnected()) {
            this._throttledSendStateUpdate(dimensionName, changes);
        }
    }
    
    recordHistory() {
        const snapshot = {
            timestamp: new Date().toISOString(),
            alpha: { ...this.alpha.values },
            beta: { ...this.beta.values },
            gamma: { ...this.gamma.values },
            delta: { ...this.delta.values }
        };
        
        this.history.push(snapshot);
        
        // LRU清理策略1：基于数量限制
        if (this.history.length > this.maxHistory) {
            this._trimHistoryByCount();
        }
        
        // LRU清理策略2：基于时间窗口
        this._trimHistoryByTime();
        
        // LRU清理策略3：基于内存使用
        this._trimHistoryByMemory();
    }
    
    /**
     * 基于数量的历史清理
     */
    _trimHistoryByCount() {
        if (this.history.length > this.maxHistory) {
            const removeCount = this.history.length - this.maxHistory;
            console.log(`[StateMatrix4D] 清理历史记录：移除 ${removeCount} 条记录（基于数量限制）`);
            this.history.splice(0, removeCount);
        }
    }
    
    /**
     * 基于时间窗口的历史清理
     */
    _trimHistoryByTime() {
        if (this.history.length === 0) return;
        
        const now = Date.now();
        const timeWindow = this.historyTimeWindow;
        const cutoffTime = new Date(now - timeWindow).toISOString();
        
        // 查找时间窗口外的第一条记录索引
        let cutoffIndex = -1;
        for (let i = 0; i < this.history.length; i++) {
            if (this.history[i].timestamp >= cutoffTime) {
                cutoffIndex = i;
                break;
            }
        }
        
        if (cutoffIndex > 0) {
            const removeCount = cutoffIndex;
            console.log(`[StateMatrix4D] 清理历史记录：移除 ${removeCount} 条记录（基于时间窗口）`);
            this.history.splice(0, removeCount);
        }
    }
    
    /**
     * 基于内存使用的历史清理
     */
    _trimHistoryByMemory() {
        try {
            const memoryUsage = this._estimateHistoryMemory();
            if (memoryUsage > this.historyMemoryThreshold) {
                // 计算需要移除的比例
                const removeRatio = 0.3; // 移除30%的记录
                const removeCount = Math.ceil(this.history.length * removeRatio);
                
                console.log(`[StateMatrix4D] 清理历史记录：移除 ${removeCount} 条记录（内存使用 ${memoryUsage} bytes > ${this.historyMemoryThreshold} bytes）`);
                this.history.splice(0, removeCount);
            }
        } catch (error) {
            console.warn('[StateMatrix4D] 内存估算失败:', error);
        }
    }
    
    /**
     * 估算历史记录的内存使用量
     */
    _estimateHistoryMemory() {
        try {
            const jsonString = JSON.stringify(this.history);
            return new Blob([jsonString]).size;
        } catch (error) {
            console.warn('[StateMatrix4D] 无法估算内存使用:', error);
            return 0;
        }
    }
    
    /**
     * 启动历史清理定时器
     */
    _startHistoryCleanupTimer() {
        // 每15分钟清理一次历史记录（优化：降低清理频率，减少CPU使用）
        this.historyCleanupInterval = setInterval(() => {
            try {
                this._trimHistoryByTime();
                this._trimHistoryByMemory();
                
                // 记录清理统计
                if (this.history.length > 0) {
                    const memoryUsage = this._estimateHistoryMemory();
                    console.log(`[StateMatrix4D] 历史记录统计：${this.history.length} 条记录，约 ${memoryUsage} bytes`);
                }
            } catch (error) {
                console.error('[StateMatrix4D] 历史清理定时器错误:', error);
            }
        }, 900000); // 15分钟 = 900000毫秒
    }
    
    /**
     * 停止历史清理定时器
     */
    _stopHistoryCleanupTimer() {
        if (this.historyCleanupInterval) {
            clearInterval(this.historyCleanupInterval);
            this.historyCleanupInterval = null;
        }
    }
    
    checkThresholds(dimensionName) {
        if (!this.thresholdCallbacks[dimensionName]) {
            return;
        }
        
        const dim = this.dimensions[dimensionName];
        const avg = this.getDimensionAverage(dimensionName);
        
        for (const [threshold, callback] of this.thresholdCallbacks[dimensionName]) {
            if (avg >= threshold) {
                try {
                    callback();
                } catch (e) {
                    console.error('Threshold callback error:', e);
                }
            }
        }
    }
    
    applyLive2DChanges(dimensionName, changes) {
        if (!this.live2DManager) {
            return;
        }
        
        const mappings = this.getStateToLive2DMappings();
        const dimChanges = changes || {};
        
        // 處理 Live2D 模式
        for (const [key, value] of Object.entries(dimChanges)) {
            const paramKey = `${dimensionName}_${key}`;
            if (mappings[paramKey]) {
                this.live2DManager.setParameter(mappings[paramKey], value);
            }
        }
        
        const dominantEmotion = this.getDominantEmotion();
        if (dominantEmotion && mappings[dominantEmotion]) {
            this.live2DManager.setExpression(dominantEmotion);
        }
        
        // 處理 Fallback 模式 - 根據主導情緒切換立繫
        if (this.live2DManager.isFallback) {
            this._applyFallbackLayers();
        }
    }
    
    /**
         * 根據主導情緒應用 fallback 模式的三層立繫渲染
         */
        _applyFallbackLayers() {
            if (!this.live2DManager || !this.live2DManager.isFallback) {
                return;
            }
            
            const dominantEmotion = this.getDominantEmotion();
            
            // 根據情感維度 (γ) 選擇表情索引
            const emotionToIndex = {
                'happy': 1,
                'sad': 2,
                'surprised': 3,
                'angry': 4,
                'shy': 5,
                'love': 6,
                'calm': 7,
                'neutral': 0
            };
            
            // 根據認知維度 (β) 和生理維度 (α) 選擇姿態索引
            let poseIndex = 0;  // 默认: idle
            
            const curiosity = this.beta.values.curiosity || 0.5;
            const arousal = this.alpha.values.arousal || 0.5;
            const focus = this.beta.values.focus || 0.5;
            
            // 根據狀態選擇姿態
            if (arousal > 0.7) {
                poseIndex = 2;  // dancing
            } else if (curiosity > 0.7) {
                poseIndex = 1;  // thinking
            } else if (focus > 0.7) {
                poseIndex = 1;  // thinking
            } else if (arousal < 0.3) {
                poseIndex = 5;  // nodding
            }
            
            // 設置表情索引
            if (dominantEmotion && emotionToIndex[dominantEmotion] !== undefined) {
                this.live2DManager.expressionIndex = emotionToIndex[dominantEmotion];
            }
            
            // 設置姿態索引
            this.live2DManager.poseIndex = poseIndex;
            
            console.log(`[StateMatrix] Applied fallback layers: expression=${this.live2DManager.expressionIndex}, pose=${this.live2DManager.poseIndex}`);
        }
        
        /**
         * 根據主導情緒應用 fallback 模式的立繫表情（舊版，保留兼容）
         */
        _applyFallbackExpression(dominantEmotion) {
            // 使用新的三層渲染系統
            this._applyFallbackLayers();
        }    
    getStateToLive2DMappings() {
        return {
            alpha_energy: 'ParamEnergy',
            alpha_comfort: 'ParamComfort',
            alpha_arousal: 'ParamArousal',
            alpha_rest_need: 'ParamRestNeed',
            alpha_vitality: 'ParamVitality',
            alpha_tension: 'ParamTension',
            
            beta_curiosity: 'ParamCuriosity',
            beta_focus: 'ParamFocus',
            beta_confusion: 'ParamConfusion',
            beta_learning: 'ParamLearning',
            beta_clarity: 'ParamClarity',
            beta_creativity: 'ParamCreativity',
            
            gamma_happiness: 'ParamHappiness',
            gamma_sadness: 'ParamSadness',
            gamma_anger: 'ParamAnger',
            gamma_fear: 'ParamFear',
            gamma_disgust: 'ParamDisgust',
            gamma_surprise: 'ParamSurprise',
            gamma_trust: 'ParamTrust',
            gamma_anticipation: 'ParamAnticipation',
            gamma_love: 'ParamLove',
            gamma_calm: 'ParamCalm',
            
            delta_attention: 'ParamAttention',
            delta_bond: 'ParamBond',
            delta_trust: 'ParamTrust',
            delta_presence: 'ParamPresence',
            delta_intimacy: 'ParamIntimacy',
            delta_engagement: 'ParamEngagement',
            
            happiness: 'expr_happy',
            sad: 'expr_sad',
            angry: 'expr_angry',
            fear: 'expr_fear',
            surprised: 'expr_surprised',
            love: 'expr_love',
            calm: 'expr_calm'
        };
    }
    
    getDominantEmotion() {
        const emotions = this.gamma.values;
        let dominant = null;
        let maxValue = 0;
        
        for (const [emotion, value] of Object.entries(emotions)) {
            if (value > maxValue) {
                maxValue = value;
                dominant = emotion;
            }
        }
        
        if (dominant === 'happiness') return 'happy';
        if (dominant === 'sadness') return 'sad';
        if (dominant === 'anger') return 'angry';
        if (dominant === 'fear') return 'fear';
        if (dominant === 'surprise') return 'surprised';
        if (dominant === 'love') return 'love';
        if (dominant === 'calm') return 'calm';
        
        return null;
    }
    
    computeInfluences() {
        const computed = {};
        
        for (const [sourceName, targets] of Object.entries(this.influenceMatrix)) {
            computed[sourceName] = {};
            const sourceDim = this.dimensions[sourceName];
            const sourceAvg = this.getDimensionAverage(sourceName);
            
            for (const [targetName, baseStrength] of Object.entries(targets)) {
                const targetDim = this.dimensions[targetName];
                const influence = baseStrength * sourceAvg * sourceDim.weight * targetDim.weight;
                computed[sourceName][targetName] = influence;
                
                this.applyInfluence(sourceName, targetName, influence);
            }
        }
        
        return computed;
    }
    
    applyInfluence(source, target, amount) {
        const sourceDim = this.dimensions[source];
        const targetDim = this.dimensions[target];
        
        if (target === 'alpha') {
            if (source === 'gamma') {
                const happiness = sourceDim.values.happiness || 0.5;
                targetDim.values.energy = Math.min(1, targetDim.values.energy + amount * happiness * 0.1);
                targetDim.values.comfort = Math.min(1, targetDim.values.comfort + amount * happiness * 0.08);
                targetDim.values.tension = Math.max(0, targetDim.values.tension - amount * happiness * 0.1);
            }
            
            if (source === 'beta') {
                const focus = sourceDim.values.focus || 0.5;
                targetDim.values.arousal = Math.min(1, targetDim.values.arousal + amount * focus * 0.05);
            }
        } else if (target === 'beta') {
            if (source === 'alpha') {
                const energy = sourceDim.values.energy || 0.5;
                targetDim.values.focus = Math.min(1, targetDim.values.focus + amount * energy * 0.1);
                targetDim.values.clarity = Math.min(1, targetDim.values.clarity + amount * energy * 0.08);
            }
            
            if (source === 'gamma') {
                const calm = sourceDim.values.calm || 0.5;
                targetDim.values.focus = Math.min(1, targetDim.values.focus + amount * calm * 0.1);
                const fear = sourceDim.values.fear || 0;
                targetDim.values.confusion = Math.min(1, targetDim.values.confusion + amount * fear * 0.15);
            }
        } else if (target === 'gamma') {
            if (source === 'alpha') {
                const comfort = sourceDim.values.comfort || 0.5;
                targetDim.values.happiness = Math.min(1, targetDim.values.happiness + amount * comfort * 0.1);
                targetDim.values.calm = Math.min(1, targetDim.values.calm + amount * comfort * 0.08);
            }
            
            if (source === 'delta') {
                const bond = sourceDim.values.bond || 0.5;
                targetDim.values.happiness = Math.min(1, targetDim.values.happiness + amount * bond * 0.12);
                targetDim.values.trust = Math.min(1, targetDim.values.trust + amount * bond * 0.1);
            }
        } else if (target === 'delta') {
            if (source === 'gamma') {
                const happiness = sourceDim.values.happiness || 0.5;
                targetDim.values.engagement = Math.min(1, targetDim.values.engagement + amount * happiness * 0.1);
                targetDim.values.presence = Math.min(1, targetDim.values.presence + amount * happiness * 0.08);
            }
            
            if (source === 'beta') {
                const curiosity = sourceDim.values.curiosity || 0.5;
                targetDim.values.attention = Math.min(1, targetDim.values.attention + amount * curiosity * 0.1);
            }
        }
        
        targetDim.timestamp = Date.now();
    }
    
    getState(dimension = null) {
        if (dimension && this.dimensions[dimension]) {
            return { ...this.dimensions[dimension].values };
        }
        
        return {
            alpha: { ...this.alpha.values },
            beta: { ...this.beta.values },
            gamma: { ...this.gamma.values },
            delta: { ...this.delta.values }
        };
    }
    
    getDimensionAverage(dimension) {
        const dim = this.dimensions[dimension];
        if (!dim) return 0;
        
        const values = Object.values(dim.values);
        return values.reduce((a, b) => a + b, 0) / values.length;
    }
    
    getDimensionAverages() {
        return {
            alpha: this.getDimensionAverage('alpha'),
            beta: this.getDimensionAverage('beta'),
            gamma: this.getDimensionAverage('gamma'),
            delta: this.getDimensionAverage('delta')
        };
    }
    
    getAnalysis() {
        const averages = this.getDimensionAverages();
        
        const overall = Object.values(averages).reduce((a, b) => a + b, 0) / 4;
        
        const wellbeing = (
            averages.alpha * 0.25 +
            averages.beta * 0.20 +
            averages.gamma * 0.35 +
            averages.delta * 0.20
        );
        
        const arousal = (
            this.alpha.values.arousal * 0.4 +
            this.gamma.values.surprise * 0.3 +
            (1 - this.gamma.values.calm) * 0.3
        );
        
        const positive = this.gamma.values.happiness + this.gamma.values.trust + this.gamma.values.love;
        const negative = this.gamma.values.sadness + this.gamma.values.anger + this.gamma.values.fear;
        const valence = (positive - negative) / 3;
        
        const dominantDim = Object.entries(averages).sort((a, b) => b[1] - a[1])[0];
        const dominantEmotion = this.getDominantEmotion();
        
        return {
            averages,
            overall,
            wellbeing,
            arousal,
            valence,
            dominant_dimension: dominantDim ? dominantDim[0] : null,
            dominant_emotion: dominantEmotion,
            update_count: this.updateCount,
            last_update: new Date(this.lastUpdate).toISOString()
        };
    }
    
    getHistory(startTime = null, endTime = null) {
        let filtered = [...this.history];
        
        if (startTime) {
            const start = new Date(startTime);
            filtered = filtered.filter(h => new Date(h.timestamp) >= start);
        }
        
        if (endTime) {
            const end = new Date(endTime);
            filtered = filtered.filter(h => new Date(h.timestamp) <= end);
        }
        
        return filtered;
    }
    
    /**
     * 分析情绪趋势
     * @param {string} dimension - 维度名称 (alpha, beta, gamma, delta)
     * @param {string} emotion - 情绪名称
     * @param {number} windowMinutes - 时间窗口（分钟）
     * @returns {Object} 趋势分析结果
     */
    analyzeTrend(dimension = 'gamma', emotion = 'happiness', windowMinutes = 60) {
        const now = Date.now();
        const windowStart = new Date(now - windowMinutes * 60 * 1000);
        
        // 获取时间窗口内的历史记录
        const historyData = this.getHistory(windowStart, now);
        
        if (historyData.length < 2) {
            return {
                trend: 'insufficient_data',
                message: 'Not enough data points for trend analysis',
                dataPoints: historyData.length
            };
        }
        
        // 提取情绪值
        const values = historyData.map(h => {
            const dim = h.dimensions[dimension];
            return dim ? dim.emotions[emotion] || 0 : 0;
        });
        
        // 计算统计信息
        const sum = values.reduce((a, b) => a + b, 0);
        const avg = sum / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);
        
        // 计算趋势（线性回归）
        const n = values.length;
        const sumX = n * (n - 1) / 2;
        const sumXY = values.reduce((sum, y, i) => sum + i * y, 0);
        const sumX2 = (n - 1) * n * (2 * n - 1) / 6;
        
        const slope = (n * sumXY - sumX * sum) / (n * sumX2 - sumX * sumX);
        
        // 判断趋势方向
        let trend, direction;
        if (Math.abs(slope) < 0.001) {
            trend = 'stable';
            direction = 0;
        } else if (slope > 0) {
            trend = 'increasing';
            direction = 1;
        } else {
            trend = 'decreasing';
            direction = -1;
        }
        
        // 计算变化率（百分比）
        const firstValue = values[0];
        const lastValue = values[values.length - 1];
        const changePercent = firstValue !== 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;
        
        // 计算波动性（标准差）
        const variance = values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / n;
        const stdDev = Math.sqrt(variance);
        
        // 判断波动程度
        let volatility;
        if (stdDev < 0.05) {
            volatility = 'low';
        } else if (stdDev < 0.15) {
            volatility = 'medium';
        } else {
            volatility = 'high';
        }
        
        return {
            trend,
            direction,
            slope,
            changePercent,
            volatility,
            stdDev,
            stats: {
                avg,
                min,
                max,
                range: max - min
            },
            dataPoints: n,
            windowMinutes,
            dimension,
            emotion,
            firstValue,
            lastValue,
            timestamps: historyData.map(h => h.timestamp)
        };
    }
    
    /**
     * 获取情绪综合报告
     * @param {number} windowMinutes - 时间窗口（分钟）
     * @returns {Object} 综合情绪报告
     */
    getEmotionReport(windowMinutes = 60) {
        const now = Date.now();
        const windowStart = new Date(now - windowMinutes * 60 * 1000);
        const historyData = this.getHistory(windowStart, now);
        
        if (historyData.length === 0) {
            return { status: 'no_data' };
        }
        
        // 分析所有维度的情绪趋势
        const dimensions = ['alpha', 'beta', 'gamma', 'delta'];
        const emotions = {
            alpha: ['energy', 'comfort', 'arousal', 'vitality'],
            beta: ['curiosity', 'focus', 'clarity', 'creativity'],
            gamma: ['happiness', 'calm', 'love', 'trust'],
            delta: ['attention', 'bond', 'intimacy', 'engagement']
        };
        
        const trends = {};
        const summaries = {};
        
        for (const dim of dimensions) {
            trends[dim] = {};
            summaries[dim] = {
                avg: {},
                trend: {},
                dominant: null
            };
            
            for (const emo of emotions[dim]) {
                const analysis = this.analyzeTrend(dim, emo, windowMinutes);
                trends[dim][emo] = analysis;
                summaries[dim].avg[emo] = analysis.stats.avg;
                summaries[dim].trend[emo] = analysis.trend;
            }
            
            // 找出主导情绪（平均最高的）
            const emotionsAvg = summaries[dim].avg;
            const dominantEmo = Object.keys(emotionsAvg).reduce((a, b) => 
                emotionsAvg[a] > emotionsAvg[b] ? a : b
            );
            summaries[dim].dominant = {
                emotion: dominantEmo,
                value: emotionsAvg[dominantEmo],
                trend: summaries[dim].trend[dominantEmo]
            };
        }
        
        // 整体情绪状态
        const latestState = historyData[historyData.length - 1];
        const overallMood = this._computeOverallMood(latestState);
        
        return {
            status: 'success',
            windowMinutes,
            dataPoints: historyData.length,
            timestamp: new Date().toISOString(),
            overallMood,
            trends,
            summaries,
            recommendations: this._generateRecommendations(summaries, overallMood)
        };
    }
    
    /**
     * 计算整体情绪状态
     */
    _computeOverallMood(state) {
        if (!state) return { mood: 'unknown', confidence: 0 };
        
        // 计算主要情绪维度的平均分
        const gammaAvg = (state.dimensions.gamma.emotions.happiness + 
                          state.dimensions.gamma.emotions.calm + 
                          state.dimensions.gamma.emotions.love + 
                          state.dimensions.gamma.emotions.trust) / 4;
        
        const alphaAvg = (state.dimensions.alpha.emotions.energy + 
                          state.dimensions.alpha.emotions.comfort + 
                          state.dimensions.alpha.emotions.arousal + 
                          state.dimensions.alpha.emotions.vitality) / 4;
        
        let mood = 'neutral';
        let confidence = 0.5;
        
        if (gammaAvg > 0.6) {
            mood = 'happy';
            confidence = 0.7 + (gammaAvg - 0.6) * 0.3;
        } else if (gammaAvg < 0.3) {
            mood = 'sad';
            confidence = 0.7 + (0.3 - gammaAvg) * 0.3;
        } else if (alphaAvg > 0.7) {
            mood = 'energetic';
            confidence = 0.7 + (alphaAvg - 0.7) * 0.3;
        } else if (alphaAvg < 0.3) {
            mood = 'tired';
            confidence = 0.7 + (0.3 - alphaAvg) * 0.3;
        } else if (state.dimensions.gamma.emotions.calm > 0.6) {
            mood = 'calm';
            confidence = 0.8;
        }
        
        return { mood, confidence: Math.min(1, confidence) };
    }
    
    /**
     * 生成建议
     */
    _generateRecommendations(summaries, overallMood) {
        const recommendations = [];
        
        // 根据整体情绪状态提供建议
        if (overallMood.mood === 'tired') {
            recommendations.push({
                type: 'rest',
                message: '看起来你需要休息一下',
                action: 'suggested休息'
            });
        } else if (overallMood.mood === 'sad') {
            recommendations.push({
                type: 'comfort',
                message: '注意到你情绪较低落',
                action: 'offered_comfort'
            });
        } else if (overallMood.mood === 'energetic') {
            recommendations.push({
                type: 'activity',
                message: '你充满活力！',
                action: 'ready_for_activity'
            });
        }
        
        // 根据情绪趋势提供建议
        if (summaries.gamma && summaries.gamma.trend.happiness === 'decreasing') {
            recommendations.push({
                type: 'attention',
                message: '你的快乐情绪在下降',
                action: 'check_in'
            });
        }
        
        return recommendations;
    }
    
    setDimensionWeight(dimension, weight) {
        if (this.dimensions[dimension]) {
            this.dimensions[dimension].weight = weight;
        }
    }
    
    setInfluenceStrength(source, target, strength) {
        if (this.influenceMatrix[source] && this.influenceMatrix[source][target] !== undefined) {
            this.influenceMatrix[source][target] = Math.max(0, Math.min(1, strength));
        }
    }
    
    registerChangeCallback(callback) {
        this.changeCallbacks.push(callback);
    }
    
    registerThresholdCallback(dimension, threshold, callback) {
        if (!this.thresholdCallbacks[dimension]) {
            this.thresholdCallbacks[dimension] = [];
        }
        this.thresholdCallbacks[dimension].push([threshold, callback]);
    }
    
    reset() {
        const defaults = {
            sadness: 0.0, anger: 0.0, fear: 0.0, disgust: 0.0, confusion: 0.0,
            tension: 0.0, intimacy: 0.0, love: 0.0, surprise: 0.0
        };
        
        for (const dim of Object.values(this.dimensions)) {
            for (const key of Object.keys(dim.values)) {
                dim.values[key] = defaults[key] !== undefined ? defaults[key] : 0.5;
            }
            dim.timestamp = Date.now();
        }
        
        this.updateCount = 0;
        this.history = [];
        this.lastUpdate = Date.now();
    }
    
    /**
     * 节流发送状态更新消息
     * @param {string} dimensionName 维度名称
     * @param {Object} changes 变更内容
     */
    _throttledSendStateUpdate(dimensionName, changes) {
        const now = Date.now();
        const message = {
            type: 'state_update',
            dimension: dimensionName,
            changes: changes,
            timestamp: now
        };
        
        // 保存待发送的消息（合并最新的变化）
        this._pendingMessage = message;
        
        // 清除之前的定时器
        if (this._messageTimer) {
            clearTimeout(this._messageTimer);
        }
        
        // 检查是否立即发送（距离上次发送超过节流间隔）
        if (now - this._lastMessageTime >= this._messageThrottleInterval) {
            this._sendStateUpdateNow();
        } else {
            // 设置定时器，在节流间隔后发送
            this._messageTimer = setTimeout(() => {
                this._sendStateUpdateNow();
            }, this._messageThrottleInterval);
        }
    }
    
    /**
     * 立即发送状态更新消息
     */
    _sendStateUpdateNow() {
        if (!this._pendingMessage) {
            return;
        }
        
        try {
            const sent = this.websocket.send(this._pendingMessage);
            if (sent) {
                this._lastMessageTime = Date.now();
                this._pendingMessage = null;
            }
        } catch (error) {
            console.error('[StateMatrix4D] 发送状态更新失败:', error);
        }
        
        // 清除定时器
        if (this._messageTimer) {
            clearTimeout(this._messageTimer);
            this._messageTimer = null;
        }
    }
    
    /**
     * 清理资源
     */
    cleanup() {
        this._stopHistoryCleanupTimer();
        
        // 清理WebSocket消息节流定时器
        if (this._messageTimer) {
            clearTimeout(this._messageTimer);
            this._messageTimer = null;
        }
        this._pendingMessage = null;
        
        this.history = [];
        this.changeCallbacks = [];
        this.thresholdCallbacks = {};
        console.log('[StateMatrix4D] 资源已清理');
    }
    
    exportToDict() {
        return {
            alpha: { ...this.alpha.values },
            beta: { ...this.beta.values },
            gamma: { ...this.gamma.values },
            delta: { ...this.delta.values },
            weights: {
                alpha: this.alpha.weight,
                beta: this.beta.weight,
                gamma: this.gamma.weight,
                delta: this.delta.weight
            },
            influence_matrix: JSON.parse(JSON.stringify(this.influenceMatrix)),
            metadata: {
                created_at: new Date(this.createdAt).toISOString(),
                last_update: new Date(this.lastUpdate).toISOString(),
                update_count: this.updateCount
            }
        };
    }
    
    importFromDict(data) {
        if (data.alpha) {
            this.alpha.values = { ...data.alpha };
        }
        if (data.beta) {
            this.beta.values = { ...data.beta };
        }
        if (data.gamma) {
            this.gamma.values = { ...data.gamma };
        }
        if (data.delta) {
            this.delta.values = { ...data.delta };
        }
        if (data.weights) {
            for (const [name, weight] of Object.entries(data.weights)) {
                if (this.dimensions[name]) {
                    this.dimensions[name].weight = weight;
                }
            }
        }
        if (data.influence_matrix) {
            this.influence_matrix = data.influence_matrix;
        }
        
        this.lastUpdate = Date.now();
    }
    
    exportToJSON() {
        return JSON.stringify(this.exportToDict(), null, 2);
    }
    
    importFromJSON(jsonStr) {
        try {
            const data = JSON.parse(jsonStr);
            this.importFromDict(data);
            return true;
        } catch (e) {
            console.error('Failed to import state from JSON:', e);
            return false;
        }
    }
    
    handleInteraction(type, data = {}) {
        try {
            switch (type) {
                case 'click':
                    this.handleInteractionClick(data);
                    break;
                case 'drag':
                    this.handleInteractionDrag(data);
                    break;
                case 'speech':
                    this.handleInteractionSpeech(data);
                    break;
                case 'touch':
                    this.handleInteractionTouch(data);
                    break;
                case 'idle':
                    this.handleInteractionIdle(data);
                    break;
                default:
                    console.warn('[StateMatrix4D] Unknown interaction type:', type);
            }
            
            this.computeInfluences();
        } catch (error) {
            console.error('[StateMatrix4D] Interaction handling failed:', error, 'type:', type, 'data:', data);
            // 即使出错也尝试计算影响，确保状态不会完全冻结
            try {
                this.computeInfluences();
            } catch (computeError) {
                console.error('[StateMatrix4D] Influence computation also failed:', computeError);
            }
        }
    }
    
    handleInteractionClick(data) {
        try {
            this.updateDelta({ attention: 1.0, engagement: 0.8 });
            this.updateBeta({ curiosity: 0.6 });
            this.updateGamma({ surprise: Math.min(1, this.gamma.values.surprise + 0.2) });
            
            if (data.part === 'head') {
                this.updateDelta({ intimacy: Math.min(1, this.delta.values.intimacy + 0.1) });
            }
        } catch (error) {
            console.error('[StateMatrix4D] Click interaction failed:', error);
        }
    }
    
    handleInteractionDrag(data) {
        try {
            this.updateDelta({ attention: 1.0, engagement: 0.9 });
            this.updateBeta({ focus: 0.7 });
            this.updateAlpha({ arousal: Math.min(1, this.alpha.values.arousal + 0.15) });
        } catch (error) {
            console.error('[StateMatrix4D] Drag interaction failed:', error);
        }
    }
    
    handleInteractionSpeech(data) {
        try {
            this.updateDelta({ attention: 1.0, engagement: 0.9, bond: Math.min(1, this.delta.values.bond + 0.05) });
            this.updateBeta({ curiosity: 0.7, learning: Math.min(1, this.beta.values.learning + 0.1) });
            
            if (data.emotion) {
                const gammaUpdate = {};
                gammaUpdate[data.emotion] = Math.min(1, this.gamma.values[data.emotion] + 0.2);
                this.updateGamma(gammaUpdate);
            }
        } catch (error) {
            console.error('[StateMatrix4D] Speech interaction failed:', error);
        }
    }
    
    handleInteractionTouch(data) {
        try {
            this.updateAlpha({ comfort: Math.min(1, this.alpha.values.comfort + 0.1) });
            this.updateDelta({ intimacy: Math.min(1, this.delta.values.intimacy + 0.15) });
            this.updateGamma({ calm: Math.min(1, this.gamma.values.calm + 0.1) });
        } catch (error) {
            console.error('[StateMatrix4D] Touch interaction failed:', error);
        }
    }
    
    handleInteractionIdle(data) {
        try {
            const duration = data.duration || 60;
            const decayFactor = Math.min(0.05, duration / 1200);
            
            this.updateBeta({
                curiosity: Math.max(0, this.beta.values.curiosity - decayFactor),
                focus: Math.max(0, this.beta.values.focus - decayFactor)
            });
            
            this.updateDelta({
                attention: Math.max(0, this.delta.values.attention - decayFactor),
                engagement: Math.max(0, this.delta.values.engagement - decayFactor)
            });
            
            this.updateGamma({ calm: Math.min(1, this.gamma.values.calm + decayFactor * 0.5) });
        } catch (error) {
            console.error('[StateMatrix4D] Idle interaction failed:', error);
        }
    }
    
    updateFromBackend(data) {
        // Update state matrix from backend data
        if (!data) return;
        
        if (data.alpha) {
            this.updateAlpha(data.alpha);
        }
        
        if (data.beta) {
            this.updateBeta(data.beta);
        }
        
        if (data.gamma) {
            this.updateGamma(data.gamma);
        }
        
        if (data.delta) {
            this.updateDelta(data.delta);
        }
        
        if (data.timestamp) {
            this.lastUpdate = data.timestamp;
        }
    }
}