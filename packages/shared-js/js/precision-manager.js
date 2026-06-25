class PrecisionManager {
    constructor(config = {}) {
        this.config = config;
        this.precisionLevel = 4;
        this.scale = 10000;
        this.cells = {};
        this.maxCells = config.max_cells || 1000000;
        this.metrics = {
            total_cells: 0,
            cells_with_memory: 0,
            avg_precision: 0.0
        };
        this.websocket = null;
        this.performanceManager = null;
        
        this.PrecisionMode = {
            INT: 0,
            DEC1: 1,
            DEC2: 2,
            DEC3: 3,
            DEC4: 4
        };
    }
    
    setWebSocket(ws) {
        this.websocket = ws;
    }
    
    setPerformanceManager(pm) {
        this.performanceManager = pm;
    }
    
    toScale(mode) {
        return Math.pow(10, mode);
    }
    
    registerCell(cellId, initialValue = 0.0) {
        if (this.cells[cellId]) {
            return this.cells[cellId];
        }
        
        const cell = {
            cell_id: cellId,
            integer_part: 0,
            memory_ref: null,
            precision_level: this.precisionLevel,
            timestamp: Date.now()
        };
        
        this.splitValue(cell, initialValue);
        this.cells[cellId] = cell;
        this.metrics.total_cells++;
        
        return cell;
    }
    
    splitValue(cell, fullValue) {
        const scale = this.toScale(cell.precision_level);
        const scaled = Math.floor(fullValue * scale);
        cell.integer_part = Math.floor(scaled / scale) * scale;
        const decimalPart = scaled % scale;
        
        if (decimalPart > 0 && !cell.memory_ref) {
            cell.memory_ref = `residual_${cell.cell_id}_${Date.now()}`;
        }
        
        return cell.integer_part;
    }
    
    reconstruct(cell, decimalValue = 0) {
        const scale = this.toScale(cell.precision_level);
        return cell.integer_part + decimalValue / scale;
    }
    
    getValue(cellId, context = null) {
        if (!this.cells[cellId]) {
            return 0.0;
        }
        
        const cell = this.cells[cellId];
        let decimalValue = 0;
        
        if (cell.memory_ref && context) {
            decimalValue = context[cell.memory_ref] || 0;
        }
        
        return this.reconstruct(cell, decimalValue);
    }
    
    setPrecision(cellId, level) {
        if (!this.cells[cellId]) {
            return false;
        }
        
        this.cells[cellId].precision_level = level;
        this.updateMetrics();
        
        return true;
    }
    
    setGlobalPrecision(level) {
        this.precisionLevel = Math.max(0, Math.min(4, level));
        this.scale = this.toScale(this.precisionLevel);
        
        console.log(`Global precision set to: ${this.getPrecisionName(this.precisionLevel)} (scale: ${this.scale})`);
        
        if (this.websocket && this.websocket.isConnected()) {
            this.websocket.send({
                type: 'precision_change',
                level: this.precisionLevel,
                name: this.getPrecisionName(this.precisionLevel),
                scale: this.scale,
                timestamp: Date.now()
            });
        }
    }
    
    getPrecisionName(level) {
        const names = {
            0: 'INT',
            1: 'DEC1',
            2: 'DEC2',
            3: 'DEC3',
            4: 'DEC4'
        };
        return names[level] || 'DEC4';
    }
    
    recommendPrecisionMode() {
        if (!this.performanceManager) {
            return this.precisionLevel;
        }
        
        const metrics = this.performanceManager.getPerformanceMetrics();
        const hardware = metrics.hardware;
        
        let recommendedLevel = 2;
        
        if (hardware.memory.total >= 16) {
            recommendedLevel = 4;
        } else if (hardware.memory.total >= 8) {
            recommendedLevel = 3;
        } else if (hardware.memory.total >= 4) {
            recommendedLevel = 2;
        } else {
            recommendedLevel = 1;
        }
        
        const avgFPS = metrics.current_fps;
        const targetFPS = metrics.target_fps;
        
        if (avgFPS < targetFPS * 0.7) {
            recommendedLevel = Math.max(0, recommendedLevel - 1);
        } else if (avgFPS > targetFPS * 1.2) {
            recommendedLevel = Math.min(4, recommendedLevel + 1);
        }
        
        return recommendedLevel;
    }
    
    autoAdjustPrecision() {
        const recommended = this.recommendPrecisionMode();
        
        if (recommended !== this.precisionLevel) {
            console.log(`Auto-adjusting precision from ${this.getPrecisionName(this.precisionLevel)} to ${this.getPrecisionName(recommended)}`);
            this.setGlobalPrecision(recommended);
        }
    }
    
    encode(dataId, value, layer = 1) {
        const precision = this.getPrecisionForLayer(layer);
        const cellId = `${dataId}_${layer}`;
        const cell = this.registerCell(cellId, value);
        
        const scale = this.toScale(precision);
        const decimalPart = Math.floor(value * scale) % scale;
        
        let residualRef = null;
        if (decimalPart > 0) {
            residualRef = `residual_${dataId}_${layer}_${Date.now()}`;
        }
        
        return {
            data_id: dataId,
            integer_part: cell.integer_part,
            decimal_ref: residualRef,
            precision: precision,
            layer: layer,
            scale: scale
        };
    }
    
    decode(encoded, context = null) {
        const integerPart = encoded.integer_part;
        const scale = encoded.scale;
        let decimalValue = 0;
        
        if (encoded.decimal_ref && context) {
            decimalValue = context[encoded.decimal_ref] || 0;
        }
        
        return integerPart + decimalValue / scale;
    }
    
    getPrecisionForLayer(layer) {
        const layerStrategy = {
            '1-3': 4,
            '4-6': 3,
            '7-9': 2
        };
        
        if (layer >= 1 && layer <= 3) return layerStrategy['1-3'];
        if (layer >= 4 && layer <= 6) return layerStrategy['4-6'];
        if (layer >= 7 && layer <= 9) return layerStrategy['7-9'];
        
        return 4;
    }
    
    compress(dataId, targetPrecision) {
        return this.setPrecision(dataId, targetPrecision);
    }
    
    updateMetrics() {
        const precisions = Object.values(this.cells).map(c => c.precision_level);
        
        this.metrics.avg_precision = precisions.length > 0 
            ? precisions.reduce((a, b) => a + b, 0) / precisions.length 
            : 0;
        
        this.metrics.cells_with_memory = Object.values(this.cells)
            .filter(c => c.memory_ref !== null).length;
    }
    
    getMetrics() {
        this.updateMetrics();
        return { ...this.metrics };
    }
    
    getPrecisionStats() {
        const stats = {};
        
        for (let i = 0; i <= 4; i++) {
            stats[`DEC${i}`] = Object.values(this.cells)
                .filter(c => c.precision_level === i).length;
        }
        
        return {
            ...stats,
            total: Object.keys(this.cells).length,
            current_level: this.precisionLevel,
            current_name: this.getPrecisionName(this.precisionLevel),
            current_scale: this.scale
        };
    }
    
    estimateMemorySavings(targetLevel) {
        if (targetLevel >= this.precisionLevel) {
            return 0;
        }
        
        const currentScale = this.toScale(this.precisionLevel);
        const targetScale = this.toScale(targetLevel);
        const ratio = targetScale / currentScale;
        
        return Math.round((1 - ratio) * 100);
    }
    
    estimatePrecisionLoss(targetLevel) {
        if (targetLevel >= this.precisionLevel) {
            return 0;
        }
        
        const currentScale = this.toScale(this.precisionLevel);
        const targetScale = this.toScale(targetLevel);
        const maxLoss = (currentScale - targetScale) / currentScale;
        
        return (maxLoss * 100).toFixed(2) + '%';
    }
    
    optimizeForMemory(targetMemoryGB) {
        const memoryUsage = this.estimateMemoryUsage();
        
        if (memoryUsage <= targetMemoryGB) {
            return {
                success: true,
                message: 'Current precision already within memory target',
                current_precision: this.getPrecisionName(this.precisionLevel)
            };
        }
        
        const currentLevel = this.precisionLevel;
        let targetLevel = currentLevel;
        
        while (targetLevel > 0) {
            const testUsage = this.estimateMemoryUsageAtLevel(targetLevel - 1);
            if (testUsage <= targetMemoryGB) {
                targetLevel--;
            } else {
                break;
            }
        }
        
        if (targetLevel !== currentLevel) {
            this.setGlobalPrecision(targetLevel);
            return {
                success: true,
                message: `Reduced precision from ${this.getPrecisionName(currentLevel)} to ${this.getPrecisionName(targetLevel)}`,
                old_precision: this.getPrecisionName(currentLevel),
                new_precision: this.getPrecisionName(targetLevel),
                memory_saved: this.estimateMemorySavings(targetLevel),
                precision_loss: this.estimatePrecisionLoss(targetLevel)
            };
        }
        
        return {
            success: false,
            message: 'Cannot reduce precision further while maintaining acceptable precision',
            current_precision: this.getPrecisionName(this.precisionLevel)
        };
    }
    
    estimateMemoryUsage() {
        return this.estimateMemoryUsageAtLevel(this.precisionLevel);
    }
    
    estimateMemoryUsageAtLevel(level) {
        const baseMemoryPerCell = 64;
        const cellCount = Object.keys(this.cells).length;
        const precisionFactor = Math.pow(10, level) / 10000;
        
        return (cellCount * baseMemoryPerCell * precisionFactor) / (1024 * 1024);
    }
    
    reset() {
        this.cells = {};
        this.precisionLevel = 4;
        this.scale = 10000;
        this.metrics = {
            total_cells: 0,
            cells_with_memory: 0,
            avg_precision: 0.0
        };
    }
    
    exportToDict() {
        return {
            precision_level: this.precisionLevel,
            scale: this.scale,
            cells: this.cells,
            metrics: this.metrics
        };
    }
    
    importFromDict(data) {
        if (data.precision_level !== undefined) {
            this.setGlobalPrecision(data.precision_level);
        }
        if (data.cells) {
            this.cells = { ...data.cells };
        }
        if (data.metrics) {
            this.metrics = { ...data.metrics };
        }
    }
    
    saveToStorage() {
        try {
            const data = this.exportToDict();
            localStorage.setItem('angela_precision', JSON.stringify(data));
        } catch (e) {
            console.error('Failed to save precision data:', e);
        }
    }
    
    loadFromStorage() {
        try {
            const data = localStorage.getItem('angela_precision');
            if (data) {
                this.importFromDict(JSON.parse(data));
            }
        } catch (e) {
            console.error('Failed to load precision data:', e);
        }
    }
}