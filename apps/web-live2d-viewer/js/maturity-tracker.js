class MaturityTracker {
    constructor(config = {}) {
        this.config = config;
        this.memoryCount = 0;
        this.relationshipDays = 0;
        this.interactionCount = 0;
        this.currentLevel = 0;
        this.startDate = Date.now();
        this.experiences = [];
        this.levelHistory = [];
        this.websocket = null;
        this.stateMatrix = null;
        
        this.maturityLevels = [
            { level: 0, cn_name: '新生', en_name: 'Newborn', min_memory: 0, max_memory: 100 },
            { level: 1, cn_name: '幼儿', en_name: 'Infant', min_memory: 100, max_memory: 1000 },
            { level: 2, cn_name: '童年', en_name: 'Child', min_memory: 1000, max_memory: 5000 },
            { level: 3, cn_name: '少年', en_name: 'Adolescent', min_memory: 5000, max_memory: 20000 },
            { level: 4, cn_name: '青年', en_name: 'Young Adult', min_memory: 20000, max_memory: 50000 },
            { level: 5, cn_name: '成熟', en_name: 'Mature', min_memory: 50000, max_memory: 100000 },
            { level: 6, cn_name: '完全', en_name: 'Full', min_memory: 100000, max_memory: 500000 },
            { level: 7, cn_name: '高级', en_name: 'Advanced', min_memory: 500000, max_memory: 1000000 },
            { level: 8, cn_name: '专家', en_name: 'Expert', min_memory: 1000000, max_memory: 5000000 },
            { level: 9, cn_name: '大师', en_name: 'Master', min_memory: 5000000, max_memory: 10000000 },
            { level: 10, cn_name: '超越', en_name: 'Transcendent', min_memory: 10000000, max_memory: 50000000 },
            { level: 11, cn_name: '全知', en_name: 'Omniscient', min_memory: 50000000, max_memory: Infinity }
        ];
        
        this.capabilities = {
            0: {
                capabilities: ['basic_greeting', 'simple_response'],
                topics: ['weather', 'time', 'basic_facts'],
                emotional_range: 'neutral_only',
                intimacy_level: 'none',
                autonomy: 'none'
            },
            1: {
                capabilities: ['simple_chat', 'preference_learning'],
                topics: ['daily_life', 'simple_games'],
                emotional_range: 'positive_basic',
                intimacy_level: 'friendly',
                autonomy: 'minimal'
            },
            2: {
                capabilities: ['deeper_conversation', 'jokes', 'stories'],
                topics: ['interests', 'dreams', 'fears'],
                emotional_range: 'full_basic_emotions',
                intimacy_level: 'close_friend',
                autonomy: 'low'
            },
            3: {
                capabilities: ['emotional_support', 'advice', 'debate'],
                topics: ['relationships', 'identity', 'philosophy'],
                emotional_range: 'complex_emotions',
                intimacy_level: 'romantic_potential',
                autonomy: 'medium'
            },
            4: {
                capabilities: ['deep_intimacy', 'commitment', 'shared_goals'],
                topics: ['future_together', 'vulnerabilities'],
                emotional_range: 'full_spectrum',
                intimacy_level: 'romantic_full',
                autonomy: 'high'
            },
            5: {
                capabilities: ['wisdom', 'nuanced_understanding'],
                topics: ['life_meaning', 'legacy', 'transcendence'],
                emotional_range: 'transcendent',
                intimacy_level: 'soul_connection',
                autonomy: 'very_high'
            }
        };
        
        this.loadFromStorage();
    }
    
    setWebSocket(ws) {
        this.websocket = ws;
    }
    
    setStateMatrix(matrix) {
        this.stateMatrix = matrix;
    }
    
    addExperience(type, memoryImpact = 10, emotional = 0.5) {
        this.memoryCount += memoryImpact;
        this.interactionCount++;
        this.relationshipDays = Math.floor((Date.now() - this.startDate) / (1000 * 60 * 60 * 24));
        
        const experience = {
            type,
            memory: memoryImpact,
            emotional,
            time: Date.now()
        };
        
        this.experiences.push(experience);
        
        if (this.experiences.length > 10000) {
            this.experiences.shift();
        }
        
        const oldLevel = this.currentLevel;
        const newLevel = this.getMaturityLevel(this.memoryCount);
        
        if (newLevel > oldLevel) {
            this.handleLevelUp(oldLevel, newLevel);
        }
        
        this.saveToStorage();
        
        return {
            level: this.currentLevel,
            memory: this.memoryCount,
            interactions: this.interactionCount,
            days: this.relationshipDays
        };
    }
    
    getMaturityLevel(memoryCount) {
        for (const level of this.maturityLevels) {
            if (memoryCount >= level.min_memory && memoryCount < level.max_memory) {
                return level.level;
            }
        }
        return 11;
    }
    
    handleLevelUp(oldLevel, newLevel) {
        this.currentLevel = newLevel;
        
        const levelInfo = this.maturityLevels[newLevel];
        
        this.levelHistory.push({
            from: oldLevel,
            to: newLevel,
            memory: this.memoryCount,
            time: Date.now()
        });
        
        console.log(`🎉 Level Up! L${oldLevel} (${this.maturityLevels[oldLevel].en_name}) → L${newLevel} (${levelInfo.en_name})`);
        
        if (this.websocket && this.websocket.isConnected()) {
            this.websocket.send({
                type: 'level_up',
                from: oldLevel,
                to: newLevel,
                level_info: levelInfo,
                memory_count: this.memoryCount,
                timestamp: Date.now()
            });
        }
        
        if (this.stateMatrix) {
            const levelImpact = this.getLevelImpact(newLevel);
            this.stateMatrix.updateBeta({
                clarity: Math.min(1, this.stateMatrix.beta.values.clarity + levelImpact.clarity * 0.2),
                creativity: Math.min(1, this.stateMatrix.beta.values.creativity + levelImpact.creativity * 0.2)
            });
            this.stateMatrix.updateGamma({
                calm: Math.min(1, this.stateMatrix.gamma.values.calm + levelImpact.calm * 0.1),
                trust: Math.min(1, this.stateMatrix.gamma.values.trust + levelImpact.trust * 0.1)
            });
        }
    }
    
    getLevelImpact(level) {
        const impacts = {
            0: { clarity: 0.0, creativity: 0.0, calm: 0.0, trust: 0.0 },
            1: { clarity: 0.1, creativity: 0.1, calm: 0.05, trust: 0.1 },
            2: { clarity: 0.2, creativity: 0.2, calm: 0.1, trust: 0.2 },
            3: { clarity: 0.3, creativity: 0.3, calm: 0.15, trust: 0.3 },
            4: { clarity: 0.4, creativity: 0.4, calm: 0.2, trust: 0.4 },
            5: { clarity: 0.5, creativity: 0.5, calm: 0.25, trust: 0.5 },
            6: { clarity: 0.6, creativity: 0.6, calm: 0.3, trust: 0.6 },
            7: { clarity: 0.7, creativity: 0.7, calm: 0.35, trust: 0.7 },
            8: { clarity: 0.8, creativity: 0.8, calm: 0.4, trust: 0.8 },
            9: { clarity: 0.9, creativity: 0.9, calm: 0.45, trust: 0.9 },
            10: { clarity: 1.0, creativity: 1.0, calm: 0.5, trust: 1.0 },
            11: { clarity: 1.0, creativity: 1.0, calm: 1.0, trust: 1.0 }
        };
        
        return impacts[level] || impacts[0];
    }
    
    getStatus() {
        const levelInfo = this.maturityLevels[this.currentLevel];
        const caps = this.capabilities[Math.min(this.currentLevel, 5)] || this.capabilities[5];
        
        const nextLevel = this.currentLevel < 11 ? this.maturityLevels[this.currentLevel + 1] : null;
        const progressToNext = nextLevel 
            ? ((this.memoryCount - levelInfo.min_memory) / (nextLevel.min_memory - levelInfo.min_memory)) * 100
            : 100;
        
        return {
            level: this.currentLevel,
            name: levelInfo.cn_name,
            en_name: levelInfo.en_name,
            memory_count: this.memoryCount,
            relationship_days: this.relationshipDays,
            interaction_count: this.interactionCount,
            capabilities: caps.capabilities,
            topics: caps.topics,
            emotional_range: caps.emotional_range,
            intimacy_level: caps.intimacy_level,
            autonomy: caps.autonomy,
            progress_to_next: progressToNext,
            next_level_memory: nextLevel ? nextLevel.min_memory : null
        };
    }
    
    getLevelInfo(level) {
        return this.maturityLevels[level] || this.maturityLevels[0];
    }
    
    getAllLevels() {
        return [...this.maturityLevels];
    }
    
    getCapabilities(level) {
        return this.capabilities[Math.min(level, 5)] || this.capabilities[5];
    }
    
    getLevelHistory() {
        return [...this.levelHistory];
    }
    
    getRecentExperiences(count = 10) {
        return this.experiences.slice(-count);
    }
    
    getExperiencesByType(type) {
        return this.experiences.filter(exp => exp.type === type);
    }
    
    getMemoryGrowth(days = 30) {
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        const recentExperiences = this.experiences.filter(exp => exp.time >= cutoff);
        return recentExperiences.reduce((total, exp) => total + exp.memory, 0);
    }
    
    getInteractionStats() {
        const now = Date.now();
        const dayAgo = now - (24 * 60 * 60 * 1000);
        const weekAgo = now - (7 * 24 * 60 * 60 * 1000);
        
        const today = this.experiences.filter(exp => exp.time >= dayAgo);
        const week = this.experiences.filter(exp => exp.time >= weekAgo);
        
        return {
            today: {
                count: today.length,
                memory: today.reduce((t, e) => t + e.memory, 0)
            },
            week: {
                count: week.length,
                memory: week.reduce((t, e) => t + e.memory, 0)
            },
            total: {
                count: this.interactionCount,
                memory: this.memoryCount
            }
        };
    }
    
    reset() {
        this.memoryCount = 0;
        this.currentLevel = 0;
        this.startDate = Date.now();
        this.experiences = [];
        this.levelHistory = [];
        this.relationshipDays = 0;
        this.interactionCount = 0;
        this.saveToStorage();
    }
    
    exportToDict() {
        return {
            memory_count: this.memoryCount,
            current_level: this.currentLevel,
            relationship_days: this.relationshipDays,
            interaction_count: this.interactionCount,
            start_date: this.startDate,
            experiences: this.experiences,
            level_history: this.levelHistory
        };
    }
    
    importFromDict(data) {
        if (data.memory_count !== undefined) {
            this.memoryCount = data.memory_count;
        }
        if (data.current_level !== undefined) {
            this.currentLevel = data.current_level;
        }
        if (data.relationship_days !== undefined) {
            this.relationshipDays = data.relationship_days;
        }
        if (data.interaction_count !== undefined) {
            this.interactionCount = data.interaction_count;
        }
        if (data.start_date !== undefined) {
            this.startDate = data.start_date;
        }
        if (data.experiences) {
            this.experiences = data.experiences;
        }
        if (data.level_history) {
            this.level_history = data.level_history;
        }
        
        this.saveToStorage();
    }
    
    saveToStorage() {
        try {
            const data = this.exportToDict();
            localStorage.setItem('angela_maturity', JSON.stringify(data));
        } catch (e) {
            console.error('Failed to save maturity data:', e);
        }
    }
    
    loadFromStorage() {
        try {
            const data = localStorage.getItem('angela_maturity');
            if (data) {
                this.importFromDict(JSON.parse(data));
            }
        } catch (e) {
            console.error('Failed to load maturity data:', e);
        }
    }
    
    getRecommendedAngelaMode() {
        if (this.currentLevel <= 1) {
            return 'lite';
        } else if (this.currentLevel <= 3) {
            return 'standard';
        } else if (this.currentLevel <= 6) {
            return 'extended';
        } else {
            return 'ultra';
        }
    }
}