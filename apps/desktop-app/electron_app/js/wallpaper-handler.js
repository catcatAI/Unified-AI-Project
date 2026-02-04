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
        
        // Canvas for composition
        this.compositionCanvas = null;
        this.compositionContext = null;
        
        // Live2D layer
        this.live2dLayer = null;
        
        // Cache
        this.wallpaperCache = new Map();
        
        this.initialize();
    }

    async initialize() {
        console.log('Initializing Wallpaper Handler...');
        
        // Create composition canvas
        this.compositionCanvas = document.createElement('canvas');
        this.compositionContext = this.compositionCanvas.getContext('2d');
        
        // Get current system wallpaper
        await this._getSystemWallpaper();
        
        // Setup canvas size
        this._updateCanvasSize();
        
        // Listen for window resize
        window.addEventListener('resize', this._onResize.bind(this));
        
        // Listen for theme changes
        if (window.electronAPI) {
            window.electronAPI.on('theme-changed', (data) => {
                console.log('Theme changed:', data);
            });
        }
        
        console.log('Wallpaper Handler initialized');
    }

    async loadWallpaper(imagePath) {
        console.log('Loading wallpaper:', imagePath);
        
        try {
            // Check cache first
            if (this.wallpaperCache.has(imagePath)) {
                return this.wallpaperCache.get(imagePath);
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
            this.currentWallpaper = image;
            
            if (window.electronAPI && window.electronAPI.wallpaper) {
                window.electronAPI.wallpaper.set(imagePath);
            }
            
            this.renderComposition();
        }
    }

    async setSystemWallpaper() {
        if (this.systemWallpaper) {
            this.currentWallpaper = this.systemWallpaper;
            this.renderComposition();
        }
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

    renderComposition() {
        if (!this.compositionContext) return;
        
        const width = this.compositionCanvas.width;
        const height = this.compositionCanvas.height;
        
        // Clear canvas
        this.compositionContext.clearRect(0, 0, width, height);
        
        // Draw wallpaper
        if (this.currentWallpaper) {
            this._drawImageCover(this.compositionContext, this.currentWallpaper, 0, 0, width, height);
        }
        
        // The Live2D layer is rendered on a separate canvas (live2d-canvas)
        // This function is for any additional visual effects or overlays
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
        
        const wallpaper = presets[preset];
        
        if (wallpaper instanceof Promise) {
            const result = await wallpaper;
            this.currentWallpaper = result;
            this.renderComposition();
        } else if (wallpaper) {
            this.currentWallpaper = wallpaper;
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
