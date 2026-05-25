/**
 * Angela AI - Gesture Manager
 * 
 * 复杂手势识别系统 - 双击、长按、捏合
 * 
 * 功能：
 * - 双击检测（双击间隔可配置）
 * - 长按检测（长按时长可配置）
 * - 捏合检测（双指缩放）
 * - 滑动检测（上下左右）
 * - 手势事件回调
 * - 手势统计和调试
 */

class GestureManager {
    constructor(options = {}) {
        // ============================================================
        // 配置
        // ============================================================
        this.config = {
            // 双击配置
            doubleTap: {
                enabled: true,
                interval: 300,        // 双击间隔（毫秒）
                maxDistance: 50,      // 最大移动距离（像素）
                threshold: 2          // 连续点击次数
            },
            
            // 长按配置
            longPress: {
                enabled: true,
                duration: 800,        // 长按时长（毫秒）
                maxDistance: 20       // 最大移动距离（像素）
            },
            
            // 捏合配置
            pinch: {
                enabled: true,
                minDistance: 10,      // 最小起始距离（像素）
                threshold: 10         // 捏合阈值（像素）
            },
            
            // 滑动配置
            swipe: {
                enabled: true,
                minDistance: 50,      // 最小滑动距离（像素）
                maxDuration: 500,     // 最大滑动时长（毫秒）
                minVelocity: 0.3      // 最小滑动速度（像素/毫秒）
            }
        };

        // ============================================================
        // 状态跟踪
        // ============================================================
        this.state = {
            // 双击状态
            lastTap: null,           // 最后一次点击 {x, y, time}
            tapCount: 0,             // 点击计数
            tapTimer: null,          // 双击定时器
            
            // 长按状态
            longPressTimer: null,    // 长按定时器
            longPressStart: null,    // 长按起始 {x, y, time}
            isLongPressing: false,   // 是否正在长按
            
            // 捏合状态
            pinchStartDistance: null,// 捏合起始距离
            pinchCenter: null,       // 捏合中心点
            activeTouches: [],       // 活跃触摸点
            
            // 滑动状态
            swipeStart: null,        // 滑动起始 {x, y, time}
            swipeEnd: null,          // 滑动结束 {x, y, time}
            isSwiping: false         // 是否正在滑动
        };

        // ============================================================
        // 事件监听器
        // ============================================================
        this.listeners = {
            doubleTap: [],
            longPress: [],
            longPressCancel: [],
            pinch: [],
            pinchStart: [],
            pinchEnd: [],
            swipe: [],
            swipeStart: [],
            swipeEnd: []
        };

        // ============================================================
        // 统计
        // ============================================================
        this.stats = {
            doubleTap: 0,
            longPress: 0,
            pinch: 0,
            swipe: 0,
            totalGestures: 0
        };

        console.log('[GestureManager] Initialized');
    }

    // ================================================================
    // 事件处理
    // ================================================================

    /**
     * 处理触摸开始
     */
    handleTouchStart(event) {
        const touches = event.touches || event.changedTouches;
        
        // 单指触摸
        if (touches.length === 1) {
            const touch = touches[0];
            this._handleSingleTouchStart(touch);
        }
        // 双指触摸 - 捏合
        else if (touches.length === 2 && this.config.pinch.enabled) {
            this._handlePinchStart(touches);
        }
    }

    /**
     * 处理触摸移动
     */
    handleTouchMove(event) {
        const touches = event.touches || event.changedTouches;
        
        // 单指触摸移动
        if (touches.length === 1) {
            const touch = touches[0];
            this._handleSingleTouchMove(touch);
        }
        // 双指触摸移动 - 捏合
        else if (touches.length === 2 && this.config.pinch.enabled) {
            this._handlePinchMove(touches);
        }
    }

    /**
     * 处理触摸结束
     */
    handleTouchEnd(event) {
        const touches = event.changedTouches;
        
        // 单指触摸结束
        if (touches.length === 1) {
            const touch = touches[0];
            this._handleSingleTouchEnd(touch);
        }
        // 双指触摸结束 - 捏合结束
        else if (touches.length === 2 && this.config.pinch.enabled) {
            this._handlePinchEnd(touches);
        }
    }

    // ================================================================
    // 单指手势处理
    // ================================================================

    _handleSingleTouchStart(touch) {
        const x = touch.clientX;
        const y = touch.clientY;
        const time = Date.now();

        // 双击检测
        if (this.config.doubleTap.enabled) {
            this._checkDoubleTap(x, y, time);
        }

        // 长按检测
        if (this.config.longPress.enabled) {
            this._startLongPress(x, y, time);
        }

        // 滑动检测
        if (this.config.swipe.enabled) {
            this.state.swipeStart = { x, y, time };
            this.state.isSwiping = true;
        }
    }

    _handleSingleTouchMove(touch) {
        const x = touch.clientX;
        const y = touch.clientY;

        // 长按移动检查
        if (this.state.isLongPressing && this.state.longPressStart) {
            const distance = this._calculateDistance(x, y, this.state.longPressStart.x, this.state.longPressStart.y);
            if (distance > this.config.longPress.maxDistance) {
                this._cancelLongPress();
            }
        }

        // 滑动检测
        if (this.state.isSwiping && this.state.swipeStart) {
            const distance = this._calculateDistance(x, y, this.state.swipeStart.x, this.state.swipeStart.y);
            if (distance > this.config.swipe.minDistance) {
                this._notifySwipeStart({
                    startX: this.state.swipeStart.x,
                    startY: this.state.swipeStart.y,
                    currentX: x,
                    currentY: y,
                    direction: this._calculateDirection(
                        this.state.swipeStart.x, this.state.swipeStart.y,
                        x, y
                    )
                });
            }
        }
    }

    _handleSingleTouchEnd(touch) {
        const x = touch.clientX;
        const y = touch.clientY;
        const time = Date.now();

        // 取消长按
        if (this.state.isLongPressing) {
            this._cancelLongPress();
        }

        // 滑动检测
        if (this.state.isSwiping && this.state.swipeStart) {
            this._checkSwipe(x, y, time);
            this.state.isSwiping = false;
            this.state.swipeStart = null;
        }
    }

    // ================================================================
    // 双击检测
    // ================================================================

    _checkDoubleTap(x, y, time) {
        const { interval, maxDistance, threshold } = this.config.doubleTap;

        // 检查是否在双击间隔内
        if (this.state.lastTap) {
            const timeDiff = time - this.state.lastTap.time;
            const distance = this._calculateDistance(x, y, this.state.lastTap.x, this.state.lastTap.y);

            if (timeDiff < interval && distance < maxDistance) {
                this.state.tapCount++;

                // 达到双击阈值
                if (this.state.tapCount >= threshold) {
                    this._notifyDoubleTap({ x, y, time });
                    this._resetDoubleTap();
                    return;
                }
            } else {
                // 超出间隔或距离，重置
                this._resetDoubleTap();
            }
        }

        // 更新最后点击
        this.state.lastTap = { x, y, time };
        this.state.tapCount = 1;

        // 设置双击定时器
        if (this.state.tapTimer) {
            clearTimeout(this.state.tapTimer);
        }

        this.state.tapTimer = setTimeout(() => {
            this._resetDoubleTap();
        }, interval);
    }

    _resetDoubleTap() {
        this.state.lastTap = null;
        this.state.tapCount = 0;
        if (this.state.tapTimer) {
            clearTimeout(this.state.tapTimer);
            this.state.tapTimer = null;
        }
    }

    _notifyDoubleTap(data) {
        console.log('[GestureManager] DoubleTap detected:', data);
        this.stats.doubleTap++;
        this.stats.totalGestures++;
        this._emit('doubleTap', data);
    }

    // ================================================================
    // 长按检测
    // ================================================================

    _startLongPress(x, y, time) {
        this.state.longPressStart = { x, y, time };
        this.state.isLongPressing = true;

        if (this.state.longPressTimer) {
            clearTimeout(this.state.longPressTimer);
        }

        this.state.longPressTimer = setTimeout(() => {
            if (this.state.isLongPressing) {
                this._notifyLongPress({ x, y, time });
            }
        }, this.config.longPress.duration);
    }

    _cancelLongPress() {
        if (this.state.isLongPressing) {
            this._notifyLongPressCancel({
                x: this.state.longPressStart.x,
                y: this.state.longPressStart.y
            });
        }
        
        this.state.isLongPressing = false;
        this.state.longPressStart = null;
        
        if (this.state.longPressTimer) {
            clearTimeout(this.state.longPressTimer);
            this.state.longPressTimer = null;
        }
    }

    _notifyLongPress(data) {
        console.log('[GestureManager] LongPress detected:', data);
        this.stats.longPress++;
        this.stats.totalGestures++;
        this._emit('longPress', data);
    }

    _notifyLongPressCancel(data) {
        this._emit('longPressCancel', data);
    }

    // ================================================================
    // 捏合检测
    // ================================================================

    _handlePinchStart(touches) {
        const touch1 = touches[0];
        const touch2 = touches[1];

        const distance = this._calculateDistance(
            touch1.clientX, touch1.clientY,
            touch2.clientX, touch2.clientY
        );

        if (distance < this.config.pinch.minDistance) {
            return; // 距离太小，忽略
        }

        this.state.pinchStartDistance = distance;
        this.state.pinchCenter = {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };
        this.state.activeTouches = [touch1, touch2];

        this._notifyPinchStart({
            center: this.state.pinchCenter,
            distance: distance
        });
    }

    _handlePinchMove(touches) {
        if (!this.state.pinchStartDistance) {
            return;
        }

        const touch1 = touches[0];
        const touch2 = touches[1];

        const distance = this._calculateDistance(
            touch1.clientX, touch1.clientY,
            touch2.clientX, touch2.clientY
        );

        const scale = distance / this.state.pinchStartDistance;
        const center = {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };

        this._notifyPinch({
            center: center,
            scale: scale,
            distance: distance,
            direction: scale > 1 ? 'out' : 'in'
        });
    }

    _handlePinchEnd(touches) {
        if (!this.state.pinchStartDistance) {
            return;
        }

        const touch1 = touches[0];
        const touch2 = touches[1];

        const distance = this._calculateDistance(
            touch1.clientX, touch1.clientY,
            touch2.clientX, touch2.clientY
        );

        const scale = distance / this.state.pinchStartDistance;

        this._notifyPinchEnd({
            center: this.state.pinchCenter,
            scale: scale,
            distance: distance
        });

        this.state.pinchStartDistance = null;
        this.state.pinchCenter = null;
        this.state.activeTouches = [];
    }

    _notifyPinchStart(data) {
        console.log('[GestureManager] PinchStart detected:', data);
        this._emit('pinchStart', data);
    }

    _notifyPinch(data) {
        if (Math.abs(data.scale - 1) > this.config.pinch.threshold / 100) {
            this._emit('pinch', data);
        }
    }

    _notifyPinchEnd(data) {
        console.log('[GestureManager] PinchEnd detected:', data);
        this.stats.pinch++;
        this.stats.totalGestures++;
        this._emit('pinchEnd', data);
    }

    // ================================================================
    // 滑动检测
    // ================================================================

    _checkSwipe(x, y, time) {
        if (!this.state.swipeStart) {
            return;
        }

        const start = this.state.swipeStart;
        const distance = this._calculateDistance(x, y, start.x, start.y);
        const duration = time - start.time;
        const velocity = distance / duration;

        // 检查是否满足滑动条件
        if (distance >= this.config.swipe.minDistance &&
            duration <= this.config.swipe.maxDuration &&
            velocity >= this.config.swipe.minVelocity) {
            
            const direction = this._calculateDirection(start.x, start.y, x, y);
            
            this._notifySwipe({
                startX: start.x,
                startY: start.y,
                endX: x,
                endY: y,
                distance: distance,
                duration: duration,
                velocity: velocity,
                direction: direction
            });
        }
    }

    _notifySwipeStart(data) {
        this._emit('swipeStart', data);
    }

    _notifySwipe(data) {
        console.log('[GestureManager] Swipe detected:', data);
        this.stats.swipe++;
        this.stats.totalGestures++;
        this._emit('swipe', data);
    }

    // ================================================================
    // 工具方法
    // ================================================================

    _calculateDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }

    _calculateDirection(x1, y1, x2, y2) {
        const dx = x2 - x1;
        const dy = y2 - y1;
        const absDx = Math.abs(dx);
        const absDy = Math.abs(dy);

        if (absDx > absDy) {
            return dx > 0 ? 'right' : 'left';
        } else {
            return dy > 0 ? 'down' : 'up';
        }
    }

    // ================================================================
    // 事件监听器管理
    // ================================================================

    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    }

    off(event, callback) {
        if (this.listeners[event]) {
            const index = this.listeners[event].indexOf(callback);
            if (index > -1) {
                this.listeners[event].splice(index, 1);
            }
        }
    }

    _emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('[GestureManager] Error in listener:', error);
                }
            });
        }
    }

    // ================================================================
    // 配置管理
    // ================================================================

    setConfig(key, value) {
        if (key in this.config) {
            this.config[key] = { ...this.config[key], ...value };
            console.log('[GestureManager] Config updated:', key, this.config[key]);
        }
    }

    getConfig() {
        return JSON.parse(JSON.stringify(this.config));
    }

    // ================================================================
    // 统计和调试
    // ================================================================

    getStats() {
        return { ...this.stats };
    }

    resetStats() {
        this.stats = {
            doubleTap: 0,
            longPress: 0,
            pinch: 0,
            swipe: 0,
            totalGestures: 0
        };
    }

    getStatus() {
        return {
            config: this.getConfig(),
            stats: this.getStats(),
            state: {
                isLongPressing: this.state.isLongPressing,
                isSwiping: this.state.isSwiping,
                pinchActive: this.state.pinchStartDistance !== null
            }
        };
    }

    // ================================================================
    // 销毁
    // ================================================================

    destroy() {
        // 清理定时器
        if (this.state.tapTimer) {
            clearTimeout(this.state.tapTimer);
        }
        if (this.state.longPressTimer) {
            clearTimeout(this.state.longPressTimer);
        }

        // 清理监听器
        for (const event in this.listeners) {
            this.listeners[event] = [];
        }

        // 重置状态
        this.state = {
            lastTap: null,
            tapCount: 0,
            tapTimer: null,
            longPressTimer: null,
            longPressStart: null,
            isLongPressing: false,
            pinchStartDistance: null,
            pinchCenter: null,
            activeTouches: [],
            swipeStart: null,
            swipeEnd: null,
            isSwiping: false
        };

        console.log('[GestureManager] Destroyed');
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GestureManager;
}