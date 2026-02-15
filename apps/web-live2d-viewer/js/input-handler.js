/**
 * =============================================================================
 * ANGELA-MATRIX: L5[存在感层] γ [C] L1+
# =============================================================================
 *
 * 职责: 处理鼠标追踪、点击、手势和触摸交互
 * 维度: 主要涉及物理维度 (γ) 的位置、速度和碰撞检测
 * 安全: 使用 Key C (桌面同步) 进行本地输入处理
 * 成熟度: L1+ 等级即可使用基本交互功能
 *
 * 功能:
 * - 鼠标追踪
 * - 点击检测
 * - 拖拽处理
 * - 手势识别
 * - 触摸事件处理
 * - 点击穿透区域管理
 *
 * @class InputHandler
 */

class InputHandler {
    constructor(live2dManager, clickLayer) {
        this.live2dManager = live2dManager;
        this.clickLayer = clickLayer;

        // Mouse state
        this.mousePosition = { x: 0, y: 0 };
        this.lastMousePosition = { x: 0, y: 0 };
        this.isMouseDown = false;
        this.dragStart = null;
        this.currentDrag = null;

        // Click-through regions
        this.clickableRegions = [];
        this.nonClickableRegions = [];

        // Callbacks
        this.onClick = null;
        this.onDrag = null;
        this.onHover = null;
        this.onDragEnd = null;

        // Initialize
        this.initialize();
    }

    initialize() {
        // Store bound functions for proper cleanup
        this._boundOnMouseMove = this._onMouseMove.bind(this);
        this._boundOnMouseDown = this._onMouseDown.bind(this);
        this._boundOnMouseUp = this._onMouseUp.bind(this);
        this._boundOnClick = this._onClick.bind(this);
        this._boundOnTouchStart = this._onTouchStart.bind(this);
        this._boundOnTouchMove = this._onTouchMove.bind(this);
        this._boundOnTouchEnd = this._onTouchEnd.bind(this);
        this._boundOnResize = this._onResize.bind(this);

        // Listen to mouse events on window
        window.addEventListener('mousemove', this._boundOnMouseMove);
        window.addEventListener('mousedown', this._boundOnMouseDown);
        window.addEventListener('mouseup', this._boundOnMouseUp);
        window.addEventListener('click', this._boundOnClick);

        // Touch events
        window.addEventListener('touchstart', this._boundOnTouchStart);
        window.addEventListener('touchmove', this._boundOnTouchMove);
        window.addEventListener('touchend', this._boundOnTouchEnd);

        // Window resize
        window.addEventListener('resize', this._boundOnResize);

        console.log('Input Handler initialized');
    }

    _onMouseMove(event) {
        this.lastMousePosition = { ...this.mousePosition };
        this.mousePosition = { x: event.clientX, y: event.clientY };

        // Check hover
        const hoveredRegion = this._getRegionAtPoint(this.mousePosition);

        if (hoveredRegion && this.onHover) {
            this.onHover(hoveredRegion, this.mousePosition);
        }

        // Handle drag
        if (this.isMouseDown && this.dragStart) {
            const dx = event.clientX - this.dragStart.x;
            const dy = event.clientY - this.dragStart.y;

            this.currentDrag = {
                startX: this.dragStart.x,
                startY: this.dragStart.y,
                currentX: event.clientX,
                currentY: event.clientY,
                deltaX: dx,
                deltaY: dy,
                region: this._getRegionAtPoint(this.dragStart)
            };

            if (this.onDrag) {
                this.onDrag(this.currentDrag);
            }
        }

        // Update Live2D eye tracking
        const normalizedX = (event.clientX / window.innerWidth) * 2 - 1;
        const normalizedY = (event.clientY / window.innerHeight) * 2 - 1;
        this.live2dManager.lookAt(normalizedX, normalizedY);
    }

    _onMouseDown(event) {
        this.isMouseDown = true;
        this.dragStart = { x: event.clientX, y: event.clientY };

        // Check if clicking on non-clickable region (pass through)
        const region = this._getRegionAtPoint({ x: event.clientX, y: event.clientY });

        if (!region || region.type === 'pass-through') {
            // Pass click through to desktop
            this._enableClickThrough();
        } else {
            // Intercept click
            this._disableClickThrough();
        }
    }

    _onMouseUp(event) {
        this.isMouseDown = false;

        if (this.currentDrag && this.onDragEnd) {
            this.onDragEnd(this.currentDrag);
        }

        this.currentDrag = null;
        this.dragStart = null;
    }

    _onClick(event) {
        const region = this._getRegionAtPoint({ x: event.clientX, y: event.clientY });

        if (region && region.type !== 'pass-through' && this.onClick) {
            event.preventDefault();
            event.stopPropagation();

            this.onClick(region, { x: event.clientX, y: event.clientY });
        }
    }

    _onTouchStart(event) {
        if (event.touches.length > 0) {
            const touch = event.touches[0];
            this._onMouseDown({ clientX: touch.clientX, clientY: touch.clientY });
        }
    }

    _onTouchMove(event) {
        if (event.touches.length > 0) {
            event.preventDefault();
            const touch = event.touches[0];
            this._onMouseMove({ clientX: touch.clientX, clientY: touch.clientY });
        }
    }

    _onTouchEnd(event) {
        this._onMouseUp(event);
    }

    _onResize() {
        // Update clickable regions on resize
        this._updateClickableRegions();
    }

    _getRegionAtPoint(point) {
        for (const region of this.clickableRegions) {
            if (this._isPointInRegion(point, region)) {
                return region;
            }
        }

        return null;
    }

    _isPointInRegion(point, region) {
        const left = (region.x - region.width / 2) * window.innerWidth;
        const right = (region.x + region.width / 2) * window.innerWidth;
        const top = (region.y - region.height / 2) * window.innerHeight;
        const bottom = (region.y + region.height / 2) * window.innerHeight;

        return point.x >= left && point.x <= right && point.y >= top && point.y <= bottom;
    }

    _updateClickableRegions() {
        // Get regions from Live2D model
        const modelRegions = this.live2dManager.getClickableRegions();

        this.clickableRegions = modelRegions.map(region => ({
            name: region.name,
            x: region.x,
            y: region.y,
            width: region.width,
            height: region.height,
            type: 'interactive'
        }));

        // Add non-clickable regions (transparent areas)
        this._addNonClickableRegions();

        // Update click layer visuals
        this._updateClickLayerVisuals();

        // Send regions to main process
        this._sendClickThroughRegions();
    }

    _addNonClickableRegions() {
        // Define non-clickable regions around the model
        const canvas = this.live2dManager.canvas;
        if (!canvas) return;

        // Corners and edges
        this.nonClickableRegions = [
            { name: 'top-left', x: 0.1, y: 0.1, width: 0.2, height: 0.2, type: 'pass-through' },
            { name: 'top-right', x: 0.9, y: 0.1, width: 0.2, height: 0.2, type: 'pass-through' },
            { name: 'bottom-left', x: 0.1, y: 0.9, width: 0.2, height: 0.2, type: 'pass-through' },
            { name: 'bottom-right', x: 0.9, y: 0.9, width: 0.2, height: 0.2, type: 'pass-through' }
        ];

        // Combine with clickable regions
        this.clickableRegions = [...this.clickableRegions, ...this.nonClickableRegions];
    }

    _updateClickLayerVisuals() {
        // Clear existing elements
        this.clickLayer.innerHTML = '';

        // Add clickable regions
        for (const region of this.clickableRegions) {
            const element = document.createElement('div');
            element.className = 'clickable-area';
            element.style.left = `${(region.x - region.width / 2) * 100}%`;
            element.style.top = `${(region.y - region.height / 2) * 100}%`;
            element.style.width = `${region.width * 100}%`;
            element.style.height = `${region.height * 100}%`;
            element.dataset.region = region.name;

            // Only show interactive regions in debug mode
            if (region.type !== 'interactive') {
                element.style.display = 'none';
            }

            this.clickLayer.appendChild(element);
        }
    }

    _sendClickThroughRegions() {
        // 只发送interactive区域作为skipRegions（不穿透的区域）
        const interactiveRegions = this.clickableRegions
            .filter(region => region.type === 'interactive')
            .map(region => ({
                x: region.x * window.innerWidth,
                y: region.y * window.innerHeight,
                width: region.width * window.innerWidth,
                height: region.height * window.innerHeight
            }));

        if (window.electronAPI && window.electronAPI.window) {
            window.electronAPI.window.setClickThroughRegions(interactiveRegions);
        }
    }

    _enableClickThrough() {
        if (window.electronAPI && window.electronAPI.window) {
            // Only enable click-through if we are certain the mouse is over a transparent area
            // and NOT dragging or interacting
            if (this.isMouseDown) return;

            window.electronAPI.window.setIgnoreMouseEvents(true, {
                forward: true,
                translate: false
            });
        }
    }

    _disableClickThrough() {
        if (window.electronAPI && window.electronAPI.window) {
            window.electronAPI.window.setIgnoreMouseEvents(false);
        }
    }

    // Public methods
    updateRegions() {
        this._updateClickableRegions();
    }

    showVisualFeedback(x, y) {
        // Show ripple effect at click position
        const ripple = document.createElement('div');
        ripple.id = 'visual-feedback';
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;
        document.body.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    destroy() {
        // Check if already destroyed
        if (this._isDestroyed) {
            return;
        }
        this._isDestroyed = true;

        // Remove event listeners using stored bound functions
        if (this._boundOnMouseMove) {
            window.removeEventListener('mousemove', this._boundOnMouseMove);
        }
        if (this._boundOnMouseDown) {
            window.removeEventListener('mousedown', this._boundOnMouseDown);
        }
        if (this._boundOnMouseUp) {
            window.removeEventListener('mouseup', this._boundOnMouseUp);
        }
        if (this._boundOnClick) {
            window.removeEventListener('click', this._boundOnClick);
        }
        if (this._boundOnTouchStart) {
            window.removeEventListener('touchstart', this._boundOnTouchStart);
        }
        if (this._boundOnTouchMove) {
            window.removeEventListener('touchmove', this._boundOnTouchMove);
        }
        if (this._boundOnTouchEnd) {
            window.removeEventListener('touchend', this._boundOnTouchEnd);
        }
        if (this._boundOnResize) {
            window.removeEventListener('resize', this._boundOnResize);
        }

        // Clear references
        this._boundOnMouseMove = null;
        this._boundOnMouseDown = null;
        this._boundOnMouseUp = null;
        this._boundOnClick = null;
        this._boundOnTouchStart = null;
        this._boundOnTouchMove = null;
        this._boundOnTouchEnd = null;
        this._boundOnResize = null;

        // Clear other references
        this.live2dManager = null;
        this.clickLayer = null;
        this.onClick = null;
        this.onDrag = null;
        this.onHover = null;
        this.onDragEnd = null;
        this.clickableRegions = [];
        this.nonClickableRegions = [];

        console.log('[InputHandler] Destroyed successfully');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InputHandler;
}
