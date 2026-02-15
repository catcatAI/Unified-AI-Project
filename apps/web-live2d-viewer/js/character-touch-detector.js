/**
 * =============================================================================
 * ANGELA-MATRIX: L1[生物层] α [C] L2+
 * =============================================================================
 *
 * 职责: 处理触觉输入，包括鼠标点击、触摸事件
 * 维度: 主要影响生理维度 (α) 的舒适度和紧张度
 * 安全: 使用 Key C (桌面同步) 进行本地触觉检测
 * 成熟度: L2+ 等级开始理解触觉反馈
 *
 * 触觉部位 (18 个身体部位):
 * - 头部 (head)
 * - 脸颊 (cheeks)
 * - 额头 (forehead)
 * - 眼睛 (eyes)
 * - 鼻子 (nose)
 * - 嘴巴 (mouth)
 * - 耳朵 (ears)
 * - 颈部 (neck)
 * - 肩膀 (shoulders)
 * - 手臂 (arms)
 * - 手肘 (elbows)
 * - 手掌 (palms)
 * - 胸部 (chest)
 * - 腹部 (abdomen)
 * - 背部 (back)
 * - 臀部 (hips)
 * - 大腿 (thighs)
 * - 小腿 (calves)
 *
 * 触觉灵敏度:
 * - 高灵敏度: 头部、脸颊、额头、鼻子、手掌
 * - 中灵敏度: 眼睛、耳朵、嘴巴、颈部、手臂、手肘
 * - 低灵敏度: 肩膀、胸部、腹部、背部、臀部、大腿、小腿
 *
 * @class CharacterTouchDetector
 */

class CharacterTouchDetector {
    constructor(config, unifiedDisplayMatrix = null) {
        this.config = config;
        this.udm = unifiedDisplayMatrix;  // 统一显示矩阵
        
        this.canvas = null;
        this.ctx = null;
        this.image = null;
        this.imageData = null;
        
        this.initialize();
    }
    
    async initialize() {
        console.log('[TouchDetector] Initializing...');
        
        this.canvas = document.createElement('canvas');
        
        // 使用 UDM 的资源精度，否则使用默认
        const precision = this.udm ? this.udm.getResourcePrecision() : '720p';
        const size = this._getSizeForPrecision(precision);
        
        this.canvas.width = size.width;
        this.canvas.height = size.height;
        this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
        
        await this.loadImage();
        
        console.log('[TouchDetector] Initialized:', this.canvas.width, 'x', this.canvas.height);
    }
    
    _getSizeForPrecision(precision) {
        const sizes = {
            '720p': { width: 1280, height: 720 },
            '1080p': { width: 1920, height: 1080 },
            '2k': { width: 2560, height: 1440 },
            '4k': { width: 3840, height: 2160 },
            '8k': { width: 7680, height: 4320 }
        };
        return sizes[precision] || sizes['720p'];
    }
    
    async loadImage() {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                this.image = img;
                
                // 绘制到适当大小的 canvas
                const targetSize = this._getSizeForPrecision(
                    this.udm ? this.udm.getResourcePrecision() : '720p'
                );
                this.canvas.width = targetSize.width;
                this.canvas.height = targetSize.height;
                this.ctx.drawImage(img, 0, 0, targetSize.width, targetSize.height);
                
                this.imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
                console.log('[TouchDetector] Image loaded:', this.canvas.width, 'x', this.canvas.height);
                resolve();
            };
            
            img.onerror = (e) => {
                console.error('[TouchDetector] Failed to load image:', e);
                reject(e);
            };
            
            img.src = this.config.image_path;
        });
    }
    
    /**
     * 检测触摸位置的身体部位
     * 
     * 使用方法:
     * const result = detector.detectTouch(screenX, screenY);
     * // result = { hit: true, bodyPart: 'face', intensity: 0.8, ... }
     * 
     * @param {number} screenX - 屏幕 X 坐标
     * @param {number} screenY - 屏幕 Y 坐标
     * @param {string} touchType - 触摸类型 ('pat', 'poke', 'stroke')
     * @returns {object} - 检测结果
     */
    detectTouch(screenX, screenY, touchType = 'pat') {
        if (!this.imageData) {
            return { hit: false, bodyPart: null, message: 'Touch detector not initialized' };
        }
        
        // 使用 UDM 转换坐标
        let canvasX, canvasY;
        
        if (this.udm) {
            const canvasCoords = this.udm.screenToCanvas(screenX, screenY);
            canvasX = canvasCoords.x;
            canvasY = canvasCoords.y;
        } else {
            // 没有 UDM 时直接使用
            canvasX = screenX;
            canvasY = screenY;
        }
        
        // 检查是否在角色边界内
        const bbox = this._getBoundingBox();
        if (canvasX < bbox.x || canvasX >= bbox.x + bbox.width ||
            canvasY < bbox.y || canvasY >= bbox.y + bbox.height) {
            return {
                hit: false,
                bodyPart: null,
                message: 'Touch outside character',
                coordinates: { screen: { x: screenX, y: screenY }, canvas: { x: canvasX, y: canvasY } }
            };
        }
        
        // 获取像素颜色
        const pixelColor = this._getPixelColor(canvasX, canvasY);
        
        // 检测身体部位
        const detection = this._detectBodyPart(canvasX, canvasY, pixelColor);
        
        // 计算触摸强度
        const intensity = this._calculateIntensity(pixelColor);
        
        // 获取触摸配置
        const touchConfig = this.config.touch_zones[detection.bodyPart] || {};
        
        const result = {
            hit: true,
            bodyPart: detection.bodyPart,
            description: touchConfig.description || detection.bodyPart,
            tactileType: touchConfig.tactile_type || touchType,
            expression: touchConfig.expression || 'neutral',
            paramId: touchConfig.param_id || 'PARAM_NEUTRAL',
            priority: touchConfig.priority || 1,
            colorMatch: detection.colorMatch,
            intensity: intensity,
            position: {
                screen: { x: screenX, y: screenY },
                canvas: { x: canvasX, y: canvasY }
            },
            rawColor: pixelColor,
            timestamp: Date.now()
        };
        
        // 如果有 UDM，处理完整交互流程
        if (this.udm) {
            const touchResult = this.udm.handleTouch(screenX, screenY, touchType);
            result.udmResult = touchResult;
        }
        
        return result;
    }
    
    /**
     * 检测拖动路径
     */
    detectDragPath(path, touchType = 'stroke') {
        const results = [];
        const bodyPartsHit = new Set();
        
        for (const point of path) {
            const result = this.detectTouch(point.x, point.y, touchType);
            if (result.hit) {
                results.push(result);
                bodyPartsHit.add(result.bodyPart);
            }
        }
        
        return {
            results: results,
            bodyPartsHit: Array.from(bodyPartsHit),
            dragType: this._classifyDrag(results)
        };
    }
    
    /**
     * 获取当前资源精度的边界框
     */
    _getBoundingBox() {
        const precision = this.udm ? this.udm.getResourcePrecision() : '720p';
        const scale = this._getScaleForPrecision(precision);
        
        // 原始 bbox (基于 1408x768)
        const original = this.config.character_bbox;
        
        return {
            x: original.x * scale,
            y: original.y * scale,
            width: original.width * scale,
            height: original.height * scale
        };
    }
    
    _getScaleForPrecision(precision) {
        const scales = {
            '720p': 1280 / 1408,
            '1080p': 1920 / 1408,
            '2k': 2560 / 1408,
            '4k': 3840 / 1408,
            '8k': 7680 / 1408
        };
        return scales[precision] || 1.0;
    }
    
    _getPixelColor(x, y) {
        const idx = (Math.floor(y) * this.canvas.width + Math.floor(x)) * 4;
        
        if (idx < 0 || idx >= this.imageData.data.length) {
            return { r: 0, g: 0, b: 0, a: 0 };
        }
        
        return {
            r: this.imageData.data[idx],
            g: this.imageData.data[idx + 1],
            b: this.imageData.data[idx + 2],
            a: this.imageData.data[idx + 3]
        };
    }
    
    /**
     * 检测身体部位
     */
    _detectBodyPart(x, y, pixelColor) {
        const zones = this.config.touch_zones;
        const sortedZones = Object.entries(zones)
            .map(([name, zone]) => {
                const rect = zone.rect;
                const area = (rect[2] - rect[0]) * (rect[3] - rect[1]);
                return [name, zone, area];
            })
            .sort((a, b) => {
                const priorityA = a[1].priority || 10;
                const priorityB = b[1].priority || 10;
                if (priorityA !== priorityB) return priorityA - priorityB;
                return a[2] - b[2];
            });
        
        // 转换坐标到资源空间
        const precision = this.udm ? this.udm.getResourcePrecision() : '720p';
        const scale = this._getScaleForPrecision(precision);
        
        for (const [partName, zone, area] of sortedZones) {
            const rect = zone.rect;
            const scaledX = x / scale;
            const scaledY = y / scale;
            
            if (scaledX >= rect[0] && scaledX < rect[2] && scaledY >= rect[1] && scaledY < rect[3]) {
                const colorMatch = !zone.color_range || this._checkColorInRange(pixelColor, zone.color_range);
                
                if (colorMatch || !zone.color_range) {
                    return { bodyPart: partName, colorMatch: colorMatch };
                }
            }
        }
        
        return { bodyPart: 'generic', colorMatch: false };
    }
    
    _checkColorInRange(color, colorRange) {
        if (!colorRange || colorRange.length === 0) return true;
        
        for (const range of colorRange) {
            if (Array.isArray(range[0])) {
                const [minR, minG, minB] = range[0];
                const [maxR, maxG, maxB] = range[1];
                
                if (color.r >= minR && color.r <= maxR &&
                    color.g >= minG && color.g <= maxG &&
                    color.b >= minB && color.b <= maxB) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    _calculateIntensity(pixelColor) {
        const brightness = (pixelColor.r * 0.299 + pixelColor.g * 0.587 + pixelColor.b * 0.114) / 255;
        const alpha = pixelColor.a / 255;
        return Math.round((brightness * alpha) * 100) / 100;
    }
    
    _classifyDrag(results) {
        if (results.length < 2) return 'tap';
        
        const dx = results[results.length - 1].position.canvas.x - results[0].position.canvas.x;
        const dy = results[results.length - 1].position.canvas.y - results[0].position.canvas.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance < 20) return 'tap';
        if (distance < 50) return 'short_stroke';
        return 'long_stroke';
    }
    
    getAvailableZones() {
        return Object.entries(this.config.touch_zones).map(([name, zone]) => ({
            name,
            description: zone.description,
            rect: zone.rect,
            tactileType: zone.tactile_type,
            priority: zone.priority
        }));
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CharacterTouchDetector;
}