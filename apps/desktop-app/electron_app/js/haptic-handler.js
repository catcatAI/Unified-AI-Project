/**
 * Angela AI - Haptic Handler
 * 
 * 使用 UnifiedDisplayMatrix 进行触觉计算
 */

class HapticHandler {
    constructor(unifiedDisplayMatrix = null) {
        this.udm = unifiedDisplayMatrix;  // 统一显示矩阵
        
        this.devices = [];
        this.connectedDevices = new Map();
        
        this.vibrationSupported = 'vibrate' in navigator;
        this.hidSupported = 'hid' in navigator;
        this.isEnabled = false;
        
        this.initialize();
    }

    async initialize() {
        console.log('[HapticHandler] Initializing...');
        
        if (this.vibrationSupported) {
            console.log('[HapticHandler] Vibration API supported');
        }
        
        if (this.hidSupported) {
            console.log('[HapticHandler] WebHID API supported');
            await this._scanHidDevices();
        }
        
        await this.discoverDevices();
        console.log('[HapticHandler] Initialized');
    }

    async discoverDevices() {
        if (this.hidSupported) {
            await this._scanHidDevices();
        }
        this._checkGamepads();
        await this._checkBluetoothDevices();
        
        console.log(`[HapticHandler] Found ${this.devices.length} haptic devices`);
        return this.devices;
    }

    async _scanHidDevices() {
        try {
            const devices = await navigator.hid.getDevices();
            for (const device of devices) {
                if (this._isHapticDevice(device)) {
                    this.devices.push({
                        type: 'hid',
                        device,
                        name: device.productName,
                        vendorId: device.vendorId,
                        productId: device.productId
                    });
                }
            }
        } catch (error) {
            console.error('[HapticHandler] Failed to scan HID devices:', error);
        }
    }

    _isHapticDevice(hidDevice) {
        const hapticVendors = [0x045e, 0x054c, 0x0e6f, 0x0f0d, 0x1532];
        return hapticVendors.includes(hidDevice.vendorId);
    }

    _checkGamepads() {
        const gamepads = navigator.getGamepads();
        for (const gamepad of gamepads) {
            if (gamepad && gamepad.vibrationActuator) {
                this.devices.push({
                    type: 'gamepad',
                    device: gamepad,
                    name: gamepad.id,
                    hasRumble: gamepad.vibrationActuator.type === 'dual-rumble'
                });
            }
        }
    }

    async _checkBluetoothDevices() {
        try {
            // Web Bluetooth API - requires user interaction
        } catch (error) {
            console.error('[HapticHandler] Bluetooth scan failed:', error);
        }
    }

    async connectDevice(deviceId) {
        const device = this.devices.find(d => d.id === deviceId);
        if (!device) {
            console.error('[HapticHandler] Device not found:', deviceId);
            return false;
        }
        
        try {
            if (device.type === 'hid') {
                await device.device.open();
                this.connectedDevices.set(deviceId, device);
            }
            return true;
        } catch (error) {
            console.error('[HapticHandler] Failed to connect device:', error);
            return false;
        }
    }

    async disconnectDevice(deviceId) {
        const device = this.connectedDevices.get(deviceId);
        if (!device) return;
        
        try {
            if (device.type === 'hid') {
                await device.device.close();
            }
            this.connectedDevices.delete(deviceId);
        } catch (error) {
            console.error('[HapticHandler] Failed to disconnect device:', error);
        }
    }

    /**
     * 触发触觉反馈 - 统一方法
     * 
     * 使用 UDM 计算触觉强度：
     * - 触摸强度基于像素颜色亮度
     * - 触觉强度 = baseIntensity × touchAreaRatio × dpiRatio
     * - 确保 4K 和 1080p 显示器的触觉强度一致
     * 
     * @param {string} bodyPart - 身体部位
     * @param {number} baseIntensity - 基础强度 (0-1)
     * @param {object} touchInfo - 触摸信息 { position, intensity }
     * @returns {object} - 触觉结果
     */
    trigger(bodyPart, baseIntensity = 1.0, touchInfo = {}) {
        // 使用 UDM 计算触觉强度
        let finalIntensity = baseIntensity;
        
        if (this.udm && touchInfo.position) {
            const udmHaptic = this.udm.calculateHapticIntensity(
                baseIntensity,
                touchInfo.position.canvas,
                touchInfo.touchSize || 40
            );
            finalIntensity = udmHaptic.intensity;
        }
        
        // 获取触觉模式
        const pattern = this._getPattern(bodyPart, finalIntensity);
        
        // 触发振动
        this.vibrate(pattern.duration, pattern.intensity);
        
        return {
            bodyPart,
            duration: pattern.duration,
            intensity: pattern.intensity,
            timestamp: Date.now()
        };
    }

    vibrate(duration, intensity = 1, pattern = []) {
        if (this.vibrationSupported) {
            if (pattern.length > 0) {
                navigator.vibrate(pattern);
            } else {
                navigator.vibrate(duration);
            }
        }
        
        for (const [deviceId, device] of this.connectedDevices) {
            if (device.type === 'gamepad' && device.hasRumble) {
                device.vibrationActuator.playEffect('dual-rumble', {
                    startDelay: 0,
                    duration,
                    weakMagnitude: intensity * 0.5,
                    strongMagnitude: intensity
                });
            }
        }
    }

    /**
     * 处理角色触摸交互
     * 
     * 完整流程：
     * 1. 接收触摸检测结果
     * 2. 使用 UDM 计算触觉强度
     * 3. 触发触觉反馈
     * 4. 发送到后端
     * 
     * @param {object} touchInfo - 触摸信息
     * @returns {object} - 处理结果
     */
    async handleCharacterTouch(touchInfo) {
        if (!touchInfo || !touchInfo.hit) return null;

        console.log('[HapticHandler] Character touch:', touchInfo.bodyPart);

        // 触发触觉反馈
        const hapticResult = this.trigger(
            touchInfo.bodyPart,
            touchInfo.intensity,
            {
                position: touchInfo.position,
                touchSize: this._getTouchSize(touchInfo.bodyPart)
            }
        );

        // 构建事件
        const tactileEvent = {
            type: 'tactile_event',
            touchType: touchInfo.tactileType,
            bodyPart: touchInfo.bodyPart,
            intensity: hapticResult.intensity,
            expression: touchInfo.expression,
            position: touchInfo.position,
            colorMatch: touchInfo.colorMatch,
            timestamp: Date.now()
        };

        // 发送到后端
        const backendWs = window.angelaApp?.backendWebSocket;
        if (backendWs && backendWs.readyState === WebSocket.OPEN) {
            try {
                backendWs.send(JSON.stringify(tactileEvent));
                console.log('[HapticHandler] Tactile event sent:', touchInfo.bodyPart);
            } catch (e) {
                console.warn('[HapticHandler] Failed to send event:', e);
            }
        }

        return {
            haptic: hapticResult,
            tactileEvent
        };
    }

    /**
     * 获取触摸区域大小（像素）
     */
    _getTouchSize(bodyPart) {
        const sizes = {
            'face': 50,
            'eyes': 30,
            'mouth': 25,
            'hair': 60,
            'neck': 40,
            'shoulders': 55,
            'torso': 70,
            'chest': 65,
            'right_hand': 35,
            'left_hand': 35,
            'right_arm': 50,
            'left_arm': 50,
            'left_leg': 60,
            'right_leg': 60,
            'generic': 40
        };
        return sizes[bodyPart] || 40;
    }

    /**
     * 获取触觉模式
     */
    _getPattern(bodyPart, intensity = 1) {
        const patterns = {
            'hair': { duration: 25, intensity: intensity * 0.5 },
            'face': { duration: 30, intensity: intensity * 0.6 },
            'eyes': { duration: 15, intensity: intensity * 0.3 },
            'mouth': { duration: 20, intensity: intensity * 0.4 },
            'neck': { duration: 35, intensity: intensity * 0.7 },
            'shoulders': { duration: 40, intensity: intensity * 0.8 },
            'torso': { duration: 45, intensity: intensity * 0.9 },
            'chest': { duration: 45, intensity: intensity * 1.0 },
            'right_hand': { duration: 20, intensity: intensity * 0.6 },
            'left_hand': { duration: 20, intensity: intensity * 0.6 },
            'right_arm': { duration: 40, intensity: intensity * 0.8 },
            'left_arm': { duration: 40, intensity: intensity * 0.8 },
            'left_leg': { duration: 45, intensity: intensity * 0.8 },
            'right_leg': { duration: 45, intensity: intensity * 0.8 },
            'generic': { duration: 30, intensity: intensity * 0.6 }
        };
        
        return patterns[bodyPart] || patterns['generic'];
    }

    // 便捷方法
    hapticClick() { this.vibrate(10, 0.5); }
    hapticHover() { this.vibrate(15, 0.3); }
    hapticTap() { this.vibrate(30, 0.8); }
    hapticNotification() { this.vibrate([100, 50, 100]); }
    
    /**
     * 基于情感的触觉反馈
     */
    hapticEmotion(emotion) {
        const patterns = {
            'happy': [100, 50, 200],
            'sad': [50, 100, 50],
            'angry': [80, 40, 80, 40, 80],
            'surprised': [150],
            'love': [200, 100, 200]
        };
        const pattern = patterns[emotion] || [100];
        this.vibrate(pattern);
    }

    getDevice(deviceId) {
        return this.devices.find(d => d.id === deviceId);
    }

    getAllDevices() {
        return [...this.devices];
    }

    getConnectedDevices() {
        return Array.from(this.connectedDevices.values());
    }

    stop() {
        if (this.vibrationSupported && navigator.vibrate) {
            navigator.vibrate(0);
        }
    }

    enable() { this.isEnabled = true; }
    disable() { this.isEnabled = false; }

    shutdown() {
        for (const [deviceId] of this.connectedDevices) {
            this.disconnectDevice(deviceId);
        }
        this.devices = [];
        this.connectedDevices.clear();
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HapticHandler;
}