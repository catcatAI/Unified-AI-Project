/**
 * LayerRenderer - 三層渲染器 v2
 * 
 * 管理三層疊加渲染系統：
 * - Layer 1: 主立繫層 (base)
 * - Layer 2: 表情疊加層 (expression)
 * - Layer 3: 姿態疊加層 (pose)
 * 
 * 修正問題：
 * 1. 修復坐標轉換邏輯錯誤（使用正確的縮放）
 * 2. 修復觸摸坐標轉換方向錯誤
 * 3. 修復觸覺區域優先級排序問題
 * 4. 添加透明背景處理
 * 5. 添加圖片透明度檢測
 */
class LayerRenderer {
    /**
     * 構造函數
     * @param {HTMLCanvasElement} canvas - 目標畫布
     * @param {object} udm - UDM 對象（可選）
     */
    constructor(canvas, udm = null) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.udm = udm;
        
        // 圖層存儲
        this.layers = {
            base: null,
            expression: null,
            pose: null
        };
        
        // 當前狀態
        this.currentState = {
            expressionIndex: 0,
            poseIndex: 0,
            baseImageId: 'fullbody_ai_assistant'
        };
        
        // 圖層渲染配置
        this.layerConfig = {
            base: { zIndex: 0, opacity: 1.0, blendMode: 'source-over', enabled: true },
            expression: { zIndex: 1, opacity: 0.95, blendMode: 'source-over', enabled: true },
            pose: { zIndex: 2, opacity: 0.5, blendMode: "source-over", enabled: true }
        };
        
        // 圖片加載標誌
        this.imagesLoaded = false;
        
        // 圖片透明度緩存
        this.imageTransparency = {};
    }
    
    /**
     * 加載圖層圖片
     * @param {object} images - ANGELA_CHARACTER_IMAGES 配置
     */
    async loadLayerImages(images) {
        this.imagesLoaded = false;
        
        try {
            // 按圖層類型加載圖片
            for (const [imageId, imageData] of Object.entries(images)) {
                const layerType = imageData.layer;
                
                if (layerType && this.layers.hasOwnProperty(layerType)) {
                    const img = await this._loadImageWithTransparencyCheck(imageData.path, imageId);
                    this.layers[layerType] = {
                        image: img.image,
                        config: imageData,
                        imageId: imageId,
                        hasTransparency: img.hasTransparency
                    };
                    console.log(`[LayerRenderer] Loaded ${layerType} layer: ${imageId}, transparency: ${img.hasTransparency}`);
                }
            }
            
            this.imagesLoaded = true;
            console.log('[LayerRenderer] All layers loaded successfully');
            return true;
        } catch (error) {
            console.error('[LayerRenderer] Error loading layers:', error);
            return false;
        }
    }
    
    /**
     * 加載單張圖片並檢查透明度
     * @param {string} path - 圖片路徑
     * @param {string} imageId - 圖片ID
     * @returns {Promise<{image: HTMLImageElement, hasTransparency: boolean}>}
     */
    _loadImageWithTransparencyCheck(path, imageId) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                // 檢查透明背景
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const hasTransparency = this._checkTransparency(imageData);
                
                if (!hasTransparency) {
                    console.warn(`[LayerRenderer] Image ${path} has no transparent pixels`);
                }
                
                // 緩存透明度信息
                this.imageTransparency[imageId] = hasTransparency;
                
                resolve({ image: img, hasTransparency: hasTransparency });
            };
            img.onerror = (e) => reject(new Error(`Failed to load image: ${path}`));
            img.src = path;
        });
    }
    
    /**
     * 檢查圖片數據是否有透明像素
     * @param {ImageData} imageData - 圖片數據
     * @returns {boolean}
     */
    _checkTransparency(imageData) {
        for (let i = 3; i < imageData.data.length; i += 4) {
            if (imageData.data[i] < 255) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * 設置表情索引
     * @param {number} index - 表情索引
     */
    setExpressionIndex(index) {
        this.currentState.expressionIndex = index;
    }
    
    /**
     * 設置姿態索引
     * @param {number} index - 姿態索引
     */
    setPoseIndex(index) {
        this.currentState.poseIndex = index;
    }
    
    /**
     * 渲染所有圖層
     */
    /**
     * 渲染所有圖層（修正版 - 支持頭部和手部遮罩）
     */
    render() {
        if (!this.imagesLoaded) {
            console.warn('[LayerRenderer] Images not loaded yet, skipping render');
            return;
        }
        
        // 清空畫布
        this.ctx.fillStyle = '#1a1a1e';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 1. 渲染基礎層
        if (this.layers.base && this.layerConfig.base.enabled) {
            this._renderLayer('base');
        }
        
        // 2. 如果姿態層啟用，去除基礎層的頭部和手部
        if (this.layers.pose && this.layerConfig.pose.enabled && this.layers.base) {
            this._applyMaskToBaseLayer();
        }
        
        // 3. 渲染表情層
        if (this.layers.expression && this.layerConfig.expression.enabled) {
            this._renderLayer('expression');
        }
        
        // 4. 渲染姿態層
        if (this.layers.pose && this.layerConfig.pose.enabled) {
            this._renderLayer('pose');
        }
    }
    
    /**
     * 渲染單個圖層
     * @param {string} layerType - 圖層類型 ('base', 'expression', 'pose')
     */
    _renderLayer(layerType) {
        const layer = this.layers[layerType];
        const config = layer.config;
        const renderParams = config.renderParams || {};
        
        this.ctx.globalAlpha = this.layerConfig[layerType].opacity;
        this.ctx.globalCompositeOperation = this.layerConfig[layerType].blendMode;
        
        if (config.type === 'single_image') {
            // 單張圖片渲染
            this._renderSingleImage(layer.image, renderParams);
        } else if (config.type === 'sprite_sheet') {
            // Sprite sheet 渲染（使用像素對齊）
            this._renderSpriteSheet(layer.image, config, layerType, layer.hasTransparency);
        }
        
        // 重置混合模式
        this.ctx.globalCompositeOperation = 'source-over';
        this.ctx.globalAlpha = 1.0;
    }
    
    /**
     * 渲染單張圖片
     * @param {HTMLImageElement} img - 圖片對象
     * @param {object} params - 渲染參數
     */
    _renderSingleImage(img, params) {
        let targetWidth = params.targetWidth || img.width;
        let targetHeight = params.targetHeight || img.height;
        let offsetX = params.offsetX || 0;
        let offsetY = params.offsetY || 0;
        
        // 計算縮放比例以適應畫布高度
        if (params.scaleToHeight) {
            const scale = params.scaleToHeight / img.height;
            targetWidth = img.width * scale;
            targetHeight = params.scaleToHeight;
        }
        
        // 獲取顯示縮放比例
        const displayScale = this.udm ? this.udm.getUserScale() : 1.0;
        targetWidth *= displayScale;
        targetHeight *= displayScale;
        offsetX *= displayScale;
        offsetY *= displayScale;
        
        // ✅ 添加坐標四捨五入到整數，確保像素對齊
        targetWidth = Math.round(targetWidth);
        targetHeight = Math.round(targetHeight);
        offsetX = Math.round(offsetX);
        offsetY = Math.round(offsetY);
        
        // 居中顯示
        const x = Math.round((this.canvas.width - targetWidth) / 2 + offsetX);
        const y = Math.round((this.canvas.height - targetHeight) / 2 + offsetY);
        
        this.ctx.drawImage(img, x, y, targetWidth, targetHeight);
    }
    
    /**
     * 渲染 Sprite sheet（使用像素對齊）
     * @param {HTMLImageElement} img - 圖片對象
     * @param {object} config - 圖片配置
     * @param {string} layerType - 圖層類型
     * @param {boolean} hasTransparency - 是否有透明背景
     */
    _renderSpriteSheet(img, config, layerType, hasTransparency) {
        let currentIndex = 0;
        let overlayPositions = null;
        
        // 根據圖層類型確定當前索引和疊加位置
        if (layerType === 'expression') {
            currentIndex = this.currentState.expressionIndex;
            overlayPositions = config.expressionOverlayPositions;
        } else if (layerType === 'pose') {
            currentIndex = this.currentState.poseIndex;
            overlayPositions = config.poseOverlayPositions;
        }
        
        // 獲取當前表情/姿態的配置
        let currentItem = null;
        if (layerType === 'expression' && config.expressions) {
            currentItem = config.expressions[currentIndex];
        } else if (layerType === 'pose' && config.poses) {
            currentItem = config.poses[currentIndex];
        }
        
        if (!currentItem) {
            console.warn(`[LayerRenderer] No item found for ${layerType} at index ${currentIndex}`);
            return;
        }
        
        // 使用疊加位置配置（如果可用）
        if (overlayPositions && currentItem.name && overlayPositions[currentItem.name]) {
            const pos = overlayPositions[currentItem.name];
            
            // ✅ 修正：使用正確的縮放
            const displayScale = this.udm ? this.udm.getUserScale() : 1.0;
            
            // 計算目標位置和尺寸
            let targetX = pos.targetX * displayScale;
            let targetY = pos.targetY * displayScale;
            let targetWidth = pos.targetWidth * displayScale;
            let targetHeight = pos.targetHeight * displayScale;
            
            // ✅ 添加坐標四捨五入到整數，確保像素對齊
            targetX = Math.round(targetX);
            targetY = Math.round(targetY);
            targetWidth = Math.round(targetWidth);
            targetHeight = Math.round(targetHeight);
            
            // ✅ 完整的邊界檢查（確保坐標和尺寸都在畫布範圍內）
            if (targetX < 0) targetX = 0;
            if (targetY < 0) targetY = 0;
            if (targetX + targetWidth > this.canvas.width) {
                targetX = Math.max(0, this.canvas.width - targetWidth);
            }
            if (targetY + targetHeight > this.canvas.height) {
                targetY = Math.max(0, this.canvas.height - targetHeight);
            }
            
            // 應用不透明度
            const opacity = pos.opacity !== undefined ? pos.opacity : 0.9;
            this.ctx.globalAlpha = opacity * this.layerConfig[layerType].opacity;
            
            // 如果圖片沒有透明背景且配置要求使用遮罩
            if (!hasTransparency && pos.useMask) {
                // 使用色鍵去除背景
                this._renderSpriteSheetWithColorKey(
                    img,
                    pos.sourceX, pos.sourceY,
                    config.cellSize.width, config.cellSize.height,
                    targetX, targetY,
                    targetWidth, targetHeight
                );
            } else {
                // 正常渲染
                this.ctx.drawImage(
                    img,
                    pos.sourceX, pos.sourceY,  // 源位置
                    config.cellSize.width, config.cellSize.height,  // 源尺寸
                    targetX, targetY,  // 目標位置
                    targetWidth, targetHeight  // 目標尺寸
                );
            }
            
            console.log(`[LayerRenderer] Rendered ${layerType} layer: ${currentItem.name} at (${targetX}, ${targetY})`);
        } else {
            // 降級方案：使用網格位置渲染（居中）
            const grid = config.grid;
            const cellSize = config.cellSize;
            
            const gridX = currentItem.gridX || 0;
            const gridY = currentItem.gridY || 0;
            
            const sourceX = gridX * cellSize.width;
            const sourceY = gridY * 368 + 40;  // 跳過標籤區域（原始格子高度 368，標籤高度 40）
            
            // 獲取顯示縮放比例
            const displayScale = this.udm ? this.udm.getUserScale() : 1.0;
            let targetWidth = cellSize.width * displayScale;
            let targetHeight = cellSize.height * displayScale;
            
            // 居中顯示
            const targetX = (this.canvas.width - targetWidth) / 2;
            const targetY = (this.canvas.height - targetHeight) / 2;
            
            this.ctx.drawImage(
                img,
                sourceX, sourceY,
                cellSize.width, cellSize.height,
                targetX, targetY,
                targetWidth, targetHeight
            );
            
            console.warn(`[LayerRenderer] Using fallback grid rendering for ${layerType} layer: ${currentItem.name}`);
        }
    }
    
    /**
     * 使用色鍵去除背景並渲染
     * @param {HTMLImageElement} img - 圖片對象
     * @param {number} sx - 源X
     * @param {number} sy - 源Y
     * @param {number} sw - 源寬度
     * @param {number} sh - 源高度
     * @param {number} dx - 目標X
     * @param {number} dy - 目標Y
     * @param {number} dw - 目標寬度
     * @param {number} dh - 目標高度
     */
    _renderSpriteSheetWithColorKey(img, sx, sy, sw, sh, dx, dy, dw, dh) {
    // 創建臨時畫布
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = sw;
        tempCanvas.height = sh;
        const tempCtx = tempCanvas.getContext('2d');
        
        // 啟用抗鋸齒
        tempCtx.imageSmoothingEnabled = true;
        tempCtx.imageSmoothingQuality = 'high';
        
        // 繪製源圖片到臨時畫布
        tempCtx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
        
        // 獲取圖片數據
        const imageData = tempCtx.getImageData(0, 0, sw, sh);
        const data = imageData.data;
        
        // 色鍵去除背景（淺藍灰色系）
        // ✅ 修正：降低閾值從 30 到 18，避免錯誤去除角色邊緤
        const threshold = 18;
        const bgColor = { r: 205, g: 210, b: 225 };
        
        // 邊緣羽化半徑
        const featherRadius = 3;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // 計算與背景色的距離
            const distance = Math.sqrt(
                Math.pow(r - bgColor.r, 2) +
                Math.pow(g - bgColor.g, 2) +
                Math.pow(b - bgColor.b, 2)
            );
            
            // 如果接近背景顏色，設置透明度
            if (distance < threshold) {
                // 完全透明
                data[i + 3] = 0;
            } else if (distance < threshold + featherRadius) {
                // 邊緣羽化：半透明過渡
                const alpha = (distance - threshold) / featherRadius;
                data[i + 3] = Math.floor(alpha * 255);
            }
        }
        
        // 將處理後的圖片數據放回臨時畫布
        tempCtx.putImageData(imageData, 0, 0);
        
        // 繪製到目標畫布
        this.ctx.drawImage(tempCanvas, Math.round(dx), Math.round(dy), Math.round(dw), Math.round(dh));
    }
    
    /**
     * 獲取當前活動的觸覺區域
     * @returns {Array} 觸覺區域列表
     */
    getActiveTouchRegions() {
        const regions = [];
        
        // 收集姿態層的觸覺區域（最高優先級）
        if (this.layers.pose && this.layerConfig.pose.enabled) {
            const config = this.layers.pose.config;
            const poses = config.poses;
            const currentPose = poses[this.currentState.poseIndex];
            
            if (currentPose && config.poseTouchRegions) {
                const poseRegions = config.poseTouchRegions[currentPose.name];
                if (poseRegions) {
                    for (const [name, region] of Object.entries(poseRegions)) {
                        regions.push({
                            ...region,
                            name: name,
                            layer: 'pose',
                            priority: (region.priority || 1) * 10 + 3
                        });
                    }
                }
            }
        }
        
        // 收集表情層的觸覺區域
        if (this.layers.expression && this.layerConfig.expression.enabled) {
            const config = this.layers.expression.config;
            const expressions = config.expressions;
            const currentExpression = expressions[this.currentState.expressionIndex];
            
            if (currentExpression && config.expressionTouchRegions) {
                const exprRegions = config.expressionTouchRegions[currentExpression.name];
                if (exprRegions) {
                    for (const [name, region] of Object.entries(exprRegions)) {
                        regions.push({
                            ...region,
                            name: name,
                            layer: 'expression',
                            priority: (region.priority || 1) * 10 + 2
                        });
                    }
                }
            }
        }
        
        // 收集基礎層的觸覺區域
        if (this.layers.base && this.layerConfig.base.enabled) {
            const config = this.layers.base.config;
            if (config.touchRegions) {
                for (const [name, region] of Object.entries(config.touchRegions)) {
                    regions.push({
                        ...region,
                        name: name,
                        layer: 'base',
                        priority: (region.priority || 1) * 10 + 1
                    });
                }
            }
        }
        
        // ✅ 修正：按優先級降序排序（優先級高的先被檢測）
        regions.sort((a, b) => b.priority - a.priority);
        
        return regions;
    }
    
    /**
     * 檢測觸摸位置
     * @param {number} screenX - 屏幕 X 坐標
     * @param {number} screenY - 屏幕 Y 坐標
     * @returns {object|null} 觸摸結果
     */
    detectTouch(screenX, screenY) {
        const regions = this.getActiveTouchRegions();
        
        // ✅ 修正：正確使用 UDM 的坐標轉換
        let canvasX, canvasY;
        if (this.udm && typeof this.udm.screenToCanvas === 'function') {
            const coords = this.udm.screenToCanvas(screenX, screenY);
            canvasX = coords.x;
            canvasY = coords.y;
        } else {
            canvasX = screenX;
            canvasY = screenY;
        }
        
        // ✅ 添加邊界條件檢查（確保坐標在畫布範圍內）
        if (canvasX < 0 || canvasX >= this.canvas.width ||
            canvasY < 0 || canvasY >= this.canvas.height) {
            return null;  // 超出畫布範圍
        }
        
        // 檢測觸摸區域
        for (const region of regions) {
            if (canvasX >= region.x && canvasX < region.x + region.width &&
                canvasY >= region.y && canvasY < region.y + region.height) {
                return {
                    bodyPart: region.name,
                    layer: region.layer,
                    priority: region.priority,
                    sensitivity: region.sensitivity,
                    reaction: region.reaction,
                    intensity: Math.min(1.0, Math.sqrt(
                        Math.pow(canvasX - (region.x + region.width / 2), 2) +
                        Math.pow(canvasY - (region.y + region.height / 2), 2)
                    ) / Math.min(region.width, region.height))
                };
            }
        }
        
        return null;
    }
    
    /**
     * 將基礎層的頭部和手部區域設為透明
     * 避免三個頭部疊加和幽靈肢體問題
     */
    _applyMaskToBaseLayer() {
        const config = this.layers.pose.config;
        const poses = config.poses;
        const currentPose = poses[this.currentState.poseIndex];
        
        if (!currentPose || !config.poseOverlayPositions) {
            return;
        }
        
        const poseConfig = config.poseOverlayPositions[currentPose.name];
        if (!poseConfig) {
            return;
        }
        
        // 獲取顯示縮放比例
        const displayScale = this.udm ? this.udm.getUserScale() : 1.0;
        
        // 使用 destination-out 混合模式去除基礎層的頭部和手部
        this.ctx.save();
        this.ctx.globalCompositeOperation = 'destination-out';
        
        // 1. 應用頭部遮罩（如果有配置）
        if (poseConfig.headMaskRect) {
            const mask = poseConfig.headMaskRect;
            const x = Math.round(mask.x * displayScale);
            const y = Math.round(mask.y * displayScale);
            const width = Math.round(mask.width * displayScale);
            const height = Math.round(mask.height * displayScale);
            
            // 繪製頭部遮罩（完全透明）
            this.ctx.fillStyle = 'rgba(0, 0, 0, 1)';
            this.ctx.fillRect(x, y, width, height);
            
            console.log(`[LayerRenderer] Applied head mask at (${x}, ${y}, ${width}x${height})`);
        }
        
        // 2. 應用手部遮罩（如果有配置）
        if (poseConfig.handMaskRects && poseConfig.handMaskRects.length > 0) {
            for (const maskRect of poseConfig.handMaskRects) {
                const x = Math.round(maskRect.x * displayScale);
                const y = Math.round(maskRect.y * displayScale);
                const width = Math.round(maskRect.width * displayScale);
                const height = Math.round(maskRect.height * displayScale);
                
                // 繪製手部遮罩（完全透明）
                this.ctx.fillStyle = 'rgba(0, 0, 0, 1)';
                this.ctx.fillRect(x, y, width, height);
            }
            
            console.log(`[LayerRenderer] Applied ${poseConfig.handMaskRects.length} hand masks`);
        }
        
        this.ctx.restore();
    }


    /**
     * 更新圖層配置
     * @param {string} layerType - 圖層類型
     * @param {object} config - 配置對象
     */
    updateLayerConfig(layerType, config) {
        if (this.layerConfig[layerType]) {
            this.layerConfig[layerType] = {
                ...this.layerConfig[layerType],
                ...config
            };
        }
    }
    
    /**
     * 清除圖層
     */
    dispose() {
        this.layers.base = null;
        this.layers.expression = null;
        this.layers.pose = null;
        this.imagesLoaded = false;
        this.imageTransparency = {};
    }
}

// 導出到全局
if (typeof window !== 'undefined') {
    window.LayerRenderer = LayerRenderer;
}

// ES6 模塊導出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LayerRenderer;
}