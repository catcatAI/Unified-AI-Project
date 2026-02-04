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
        this.updateCount = 0;
        this.createdAt = Date.now();
        this.lastUpdate = Date.now();
        this.changeCallbacks = [];
        this.thresholdCallbacks = {};
        this.live2DManager = null;
        this.websocket = null;
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
            this.websocket.send({
                type: 'state_update',
                dimension: dimensionName,
                changes: changes,
                timestamp: Date.now()
            });
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
        
        if (this.history.length > this.maxHistory) {
            this.history.shift();
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
        }
        
        this.computeInfluences();
    }
    
    handleInteractionClick(data) {
        this.updateDelta({ attention: 1.0, engagement: 0.8 });
        this.updateBeta({ curiosity: 0.6 });
        this.updateGamma({ surprise: Math.min(1, this.gamma.values.surprise + 0.2) });
        
        if (data.part === 'head') {
            this.updateDelta({ intimacy: Math.min(1, this.delta.values.intimacy + 0.1) });
        }
    }
    
    handleInteractionDrag(data) {
        this.updateDelta({ attention: 1.0, engagement: 0.9 });
        this.updateBeta({ focus: 0.7 });
        this.updateAlpha({ arousal: Math.min(1, this.alpha.values.arousal + 0.15) });
    }
    
    handleInteractionSpeech(data) {
        this.updateDelta({ attention: 1.0, engagement: 0.9, bond: Math.min(1, this.delta.values.bond + 0.05) });
        this.updateBeta({ curiosity: 0.7, learning: Math.min(1, this.beta.values.learning + 0.1) });
        
        if (data.emotion) {
            const gammaUpdate = {};
            gammaUpdate[data.emotion] = Math.min(1, this.gamma.values[data.emotion] + 0.2);
            this.updateGamma(gammaUpdate);
        }
    }
    
    handleInteractionTouch(data) {
        this.updateAlpha({ comfort: Math.min(1, this.alpha.values.comfort + 0.1) });
        this.updateDelta({ intimacy: Math.min(1, this.delta.values.intimacy + 0.15) });
        this.updateGamma({ calm: Math.min(1, this.gamma.values.calm + 0.1) });
    }
    
    handleInteractionIdle(data) {
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
    }
}