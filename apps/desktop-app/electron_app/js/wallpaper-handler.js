/**
 * Angela AI - Wallpaper Handler
 * 
 * Manages wallpaper integration and non-destructive layer composition
 */

class WallpaperHandler {
    constructor() {
        this.currentWallpaper = null;
        this.systemWallpaper = null;
        this.userWallpaper = null;
        this.renderingMode = '2D'; // 預設 2D
        this.modeledObjects = []; // 被建模的物體
        
        // Canvas for composition
        this.compositionCanvas = null;
        this.compositionContext = null;
        
        // Live2D layer
        this.live2dLayer = null;
        
        // Cache management
        this.wallpaperCache = new Map();
        this.maxCacheSize = 10; // 限制快取數量以節省記憶體
        
        // Performance scaling
        this.performanceTier = 'medium';
        this.autoAdjustEnabled = true;
        
        this.initialize();
    }

    async initialize() {
        console.log('Initializing Wallpaper Handler...');
        
        // Create composition canvas
        this.compositionCanvas = document.createElement('canvas');
        this.compositionContext = this.compositionCanvas.getContext('2d', { alpha: true });
        
        // Get hardware performance tier
        await this._detectHardwareTier();
        
        // Get current system wallpaper
        await this._getSystemWallpaper();
        
        // Setup canvas size
        this._updateCanvasSize();
        
        // Listen for window resize
        window.addEventListener('resize', this._onResize.bind(this));
        
        // Listen for hardware changes
        if (window.electronAPI) {
            window.electronAPI.on('hardware-update', (data) => {
                if (this.autoAdjustEnabled) {
                    this._adjustToHardware(data.tier);
                }
            });
        }
        
        console.log('Wallpaper Handler initialized');
    }

    async _detectHardwareTier() {
        if (window.angelaApp && window.angelaApp.hardwareDetection) {
            const profile = await window.angelaApp.hardwareDetection.getProfile();
            this.performanceTier = profile.performanceTier || 'medium';
            this._adjustToHardware(this.performanceTier);
        }
    }

    _adjustToHardware(tier) {
        console.log(`Adjusting wallpaper rendering to ${tier} tier hardware`);
        this.performanceTier = tier;
        
        if (tier === 'low') {
            this.renderingMode = '2D';
            this.maxCacheSize = 3;
        } else if (tier === 'medium') {
            this.renderingMode = '2.5D';
            this.maxCacheSize = 10;
        } else {
            this.renderingMode = '3D';
            this.maxCacheSize = 25;
        }
        
        this.setRenderingMode(this.renderingMode);
    }

    async loadWallpaper(imagePath) {
        console.log('Loading wallpaper:', imagePath);
        
        try {
            // Check cache first
            if (this.wallpaperCache.has(imagePath)) {
                return this.wallpaperCache.get(imagePath);
            }
            
            // Manage cache size
            if (this.wallpaperCache.size >= this.maxCacheSize) {
                const firstKey = this.wallpaperCache.keys().next().value;
                this.wallpaperCache.delete(firstKey);
            }
            
            // Load image
            const image = await this._loadImage(imagePath);
            
            // Cache image
            this.wallpaperCache.set(imagePath, image);
            
            return image;
        } catch (error) {
            console.error('Failed to load wallpaper:', error);
            return null;
        }
    }

    async setWallpaper(imagePath) {
        const image = await this.loadWallpaper(imagePath);
        
        if (image) {
            this.userWallpaper = image;
            this.currentWallpaper = 'user';
            
            if (window.electronAPI && window.electronAPI.wallpaper) {
                window.electronAPI.wallpaper.set(imagePath);
            }
            
            this.renderComposition();
        }
    }

    async setSystemWallpaper() {
        if (this.systemWallpaper) {
            this.currentWallpaper = 'system';
            this.renderComposition();
        }
    }

    _getActiveWallpaper() {
        return this.currentWallpaper === 'user' ? this.userWallpaper : this.systemWallpaper;
    }

    async _getSystemWallpaper() {
        try {
            if (window.electronAPI && window.electronAPI.wallpaper) {
                const result = await window.electronAPI.wallpaper.get();
                
                if (result.systemWallpaper) {
                    this.systemWallpaper = await this.loadWallpaper(result.systemWallpaper);
                }
            }
        } catch (error) {
            console.error('Failed to get system wallpaper:', error);
        }
    }

    _loadImage(path) {
        return new Promise((resolve, reject) => {
            const image = new Image();
            image.onload = () => resolve(image);
            image.onerror = reject;
            image.src = path;
        });
    }

    _updateCanvasSize() {
        if (!this.compositionCanvas) return;
        
        const canvas = document.getElementById('live2d-canvas');
        if (!canvas) return;
        
        this.compositionCanvas.width = canvas.width;
        this.compositionCanvas.height = canvas.height;
        
        this.renderComposition();
    }

    _onResize() {
        this._updateCanvasSize();
    }

    setRenderingMode(mode) {
        console.log(`Setting rendering mode to: ${mode}`);
        this.renderingMode = mode;
        
        // 根據模式切換渲染管線
        if (mode === '3D') {
            this._setup3DScene();
        } else if (mode === '2.5D') {
            this._setup25DParallax();
        } else {
            this._setup2DCanvas();
        }
        
        this.renderComposition();
    }

    _setup2DCanvas() {
        console.log('Using 2D Canvas rendering');
        // 清除 2.5D/3D 特效
        this.compositionCanvas.style.transform = '';
        this.compositionCanvas.style.transition = 'transform 0.3s ease';
        if (this._parallaxHandler) {
            window.removeEventListener('mousemove', this._parallaxHandler);
            this._parallaxHandler = null;
        }
    }

    _setup25DParallax() {
        console.log('Setting up 2.5D Parallax effects');
        
        // 清除舊的監聽器
        if (this._parallaxHandler) {
            window.removeEventListener('mousemove', this._parallaxHandler);
        }

        this.compositionCanvas.style.transition = 'transform 0.1s ease-out';
        
        this._parallaxHandler = (e) => {
            if (this.renderingMode !== '2.5D') return;
            const x = (e.clientX / window.innerWidth - 0.5) * 30;
            const y = (e.clientY / window.innerHeight - 0.5) * 30;
            this.compositionCanvas.style.transform = `translate(${x}px, ${y}px) scale(1.1)`;
        };

        window.addEventListener('mousemove', this._parallaxHandler);
    }

    _setup3DScene() {
        console.log('Setting up 3D WebGL scene (Pseudo-3D)');
        
        // 清除舊的監聽器
        if (this._parallaxHandler) {
            window.removeEventListener('mousemove', this._parallaxHandler);
        }

        this.compositionCanvas.style.transition = 'transform 0.1s ease-out';
        
        this._parallaxHandler = (e) => {
            if (this.renderingMode !== '3D') return;
            const rotateY = (e.clientX / window.innerWidth - 0.5) * 20;
            const rotateX = (e.clientY / window.innerHeight - 0.5) * -20;
            this.compositionCanvas.parentElement.style.perspective = '1000px';
            this.compositionCanvas.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.05)`;
        };

        window.addEventListener('mousemove', this._parallaxHandler);
    }

    injectObject(objectData) {
        console.log('Injecting object into wallpaper:', objectData);
        
        const newObject = {
            id: objectData.id || Date.now(),
            name: objectData.name,
            position: objectData.position || { x: 0.5, y: 0.5, z: 0 },
            scale: objectData.scale || 1.0,
            rotation: objectData.rotation || { x: 0, y: 0, z: 0 },
            type: objectData.type || 'generic'
        };
        
        this.modeledObjects.push(newObject);
        this.renderComposition();
        
        return newObject.id;
    }

    renderComposition() {
        if (!this.compositionContext) return;
        
        const width = this.compositionCanvas.width;
        const height = this.compositionCanvas.height;
        
        // Clear canvas
        this.compositionContext.clearRect(0, 0, width, height);
        
        // 1. 繪製背景桌布
        const activeWallpaper = this._getActiveWallpaper();
        if (activeWallpaper) {
            this._drawImageCover(this.compositionContext, activeWallpaper, 0, 0, width, height);
        }

        // 2. 繪製建模物體 (根據渲染模式)
        this.modeledObjects.forEach(obj => {
            this._drawObject(obj, width, height);
        });

        // 3. 通知 UI 更新 (如果有需要)
    }

    _drawObject(obj, width, height) {
        const ctx = this.compositionContext;
        const x = obj.position.x * width;
        const y = obj.position.y * height;
        const size = 50 * obj.scale;

        ctx.save();
        ctx.translate(x, y);
        
        // 根據模式添加一些視覺效果
        if (this.renderingMode === '3D') {
            // 模擬 3D 陰影
            ctx.shadowBlur = 15;
            ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
            ctx.shadowOffsetX = 5;
            ctx.shadowOffsetY = 5;
        } else if (this.renderingMode === '2.5D') {
            ctx.shadowBlur = 5;
            ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        }

        // 繪製一個代表物體的發光球體或圖標
        const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, size);
        gradient.addColorStop(0, 'rgba(100, 200, 255, 0.8)');
        gradient.addColorStop(1, 'rgba(100, 200, 255, 0)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(0, 0, size, 0, Math.PI * 2);
        ctx.fill();

        // 繪製標籤
        ctx.fillStyle = 'white';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(obj.name || 'Object', 0, size + 15);
        
        ctx.restore();
    }

    _drawImageCover(ctx, image, x, y, w, h) {
        const imgRatio = image.width / image.height;
        const canvasRatio = w / h;
        
        let sx, sy, sWidth, sHeight;
        
        if (canvasRatio > imgRatio) {
            sWidth = image.width;
            sHeight = image.width / canvasRatio;
            sx = 0;
            sy = (image.height - sHeight) / 2;
        } else {
            sWidth = image.height * canvasRatio;
            sHeight = image.height;
            sx = (image.width - sWidth) / 2;
            sy = 0;
        }
        
        ctx.drawImage(image, sx, sy, sWidth, sHeight, x, y, w, h);
    }

    // Snapshot and export
    takeSnapshot() {
        if (!this.compositionCanvas) return null;
        
        // Combine composition canvas and Live2D canvas
        const snapshotCanvas = document.createElement('canvas');
        snapshotCanvas.width = this.compositionCanvas.width;
        snapshotCanvas.height = this.compositionCanvas.height;
        const snapshotCtx = snapshotCanvas.getContext('2d');
        
        // Draw wallpaper
        snapshotCtx.drawImage(this.compositionCanvas, 0, 0);
        
        // Draw Live2D
        const live2dCanvas = document.getElementById('live2d-canvas');
        if (live2dCanvas) {
            snapshotCtx.drawImage(live2dCanvas, 0, 0);
        }
        
        return snapshotCanvas.toDataURL('image/png');
    }

    saveSnapshot(filename = 'angela-snapshot.png') {
        const dataUrl = this.takeSnapshot();
        
        if (!dataUrl) {
            console.error('Failed to create snapshot');
            return;
        }
        
        // Download image
        const link = document.createElement('a');
        link.download = filename;
        link.href = dataUrl;
        link.click();
    }

    // Background effects
    applyEffect(effect) {
        if (!this.compositionContext) return;
        
        switch (effect) {
            case 'blur':
                this.compositionContext.filter = 'blur(5px)';
                break;
            case 'darken':
                this.compositionContext.filter = 'brightness(0.7)';
                break;
            case 'brighten':
                this.compositionContext.filter = 'brightness(1.3)';
                break;
            case 'grayscale':
                this.compositionContext.filter = 'grayscale(100%)';
                break;
            case 'none':
            default:
                this.compositionContext.filter = 'none';
                break;
        }
        
        this.renderComposition();
    }

    // Animation effects
    async animateEffect(effect, duration = 2000) {
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            switch (effect) {
                case 'fade-in':
                    this.compositionContext.globalAlpha = progress;
                    break;
                case 'fade-out':
                    this.compositionContext.globalAlpha = 1 - progress;
                    break;
                case 'pulse':
                    this.compositionContext.filter = `brightness(${1 + Math.sin(progress * Math.PI * 2) * 0.2})`;
                    break;
            }
            
            this.renderComposition();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Reset
                this.compositionContext.globalAlpha = 1;
                this.compositionContext.filter = 'none';
            }
        };
        
        requestAnimationFrame(animate);
    }

    // Preset wallpapers
    async loadPreset(preset) {
        const presets = {
            'default': this.systemWallpaper,
            'gradient': this._createGradientWallpaper(),
            'solid': this._createSolidWallpaper('#2c3e50'),
            'light': this._createSolidWallpaper('#ecf0f1'),
            'dark': this._createSolidWallpaper('#1a1a1a')
        };
        
        let wallpaper = presets[preset];
        
        if (wallpaper instanceof Promise) {
            wallpaper = await wallpaper;
        }

        if (wallpaper) {
            this.userWallpaper = wallpaper;
            this.currentWallpaper = 'user';
            this.renderComposition();
        }
    }

    async _createGradientWallpaper() {
        const canvas = document.createElement('canvas');
        canvas.width = 1920;
        canvas.height = 1080;
        const ctx = canvas.getContext('2d');
        
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        gradient.addColorStop(0, '#667eea');
        gradient.addColorStop(0.5, '#764ba2');
        gradient.addColorStop(1, '#f64f59');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        const image = await this._loadImage(canvas.toDataURL());
        return image;
    }

    async _createSolidWallpaper(color) {
        const canvas = document.createElement('canvas');
        canvas.width = 1920;
        canvas.height = 1080;
        const ctx = canvas.getContext('2d');
        
        ctx.fillStyle = color;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        const image = await this._loadImage(canvas.toDataURL());
        return image;
    }

    // Export current state
    exportState() {
        return {
            currentWallpaper: this.currentWallpaper?.src,
            systemWallpaper: this.systemWallpaper?.src,
            userWallpaper: this.userWallpaper?.src,
            cachedWallpapers: Array.from(this.wallpaperCache.keys())
        };
    }

    // Import state
    async importState(state) {
        if (state.userWallpaper) {
            await this.setWallpaper(state.userWallpaper);
        }
        
        // Restore cached wallpapers
        for (const path of state.cachedWallpapers) {
            await this.loadWallpaper(path);
        }
    }

    cleanup() {
        // Clear cache
        this.wallpaperCache.clear();
        
        // Remove event listeners
        window.removeEventListener('resize', this._onResize.bind(this));
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WallpaperHandler;
}
