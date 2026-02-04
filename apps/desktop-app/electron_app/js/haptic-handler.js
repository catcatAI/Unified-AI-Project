/**
 * Angela AI - Haptic Handler
 * 
 * Handles haptic feedback devices and tactile input/output
 */

class HapticHandler {
    constructor() {
        this.devices = [];
        this.connectedDevices = new Map();
        
        // Vibration API (WebHID fallback)
        this.vibrationSupported = 'vibrate' in navigator;
        
        // WebHID API
        this.hidSupported = 'hid' in navigator;
        
        // State
        this.isEnabled = false;
        
        this.initialize();
    }

    async initialize() {
        console.log('Initializing Haptic Handler...');
        
        // Check vibration support
        if (this.vibrationSupported) {
            console.log('Vibration API supported');
        }
        
        // Check WebHID support
        if (this.hidSupported) {
            console.log('WebHID API supported');
            await this._scanHidDevices();
        }
        
        // Auto-discover devices
        await this.discoverDevices();
        
        console.log('Haptic Handler initialized');
    }

    // Device discovery
    async discoverDevices() {
        // Scan for haptic devices
        if (this.hidSupported) {
            await this._scanHidDevices();
        }
        
        // Check for gamepads
        this._checkGamepads();
        
        // Check for Bluetooth devices
        await this._checkBluetoothDevices();
        
        console.log(`Found ${this.devices.length} haptic devices`);
        return this.devices;
    }

    async _scanHidDevices() {
        try {
            const devices = await navigator.hid.getDevices();
            
            for (const device of devices) {
                // Filter for haptic devices
                if (this._isHapticDevice(device)) {
                    this.devices.push({
                        type: 'hid',
                        device: device,
                        name: device.productName,
                        vendorId: device.vendorId,
                        productId: device.productId
                    });
                }
            }
        } catch (error) {
            console.error('Failed to scan HID devices:', error);
        }
    }

    _isHapticDevice(hidDevice) {
        // Check vendor/product IDs for known haptic devices
        const hapticVendors = [
            0x045e, // Microsoft (Xbox controllers)
            0x054c, // Sony (PlayStation controllers)
            0x0e6f, // PDP
            0x0f0d, // Hori
            0x1532  // Razer
        ];
        
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
        // Web Bluetooth API for haptic devices
        try {
            // Request device (requires user interaction)
            // device = await navigator.bluetooth.requestDevice({
            //     filters: [{ services: ['battery_service'] }]
            // });
        } catch (error) {
            console.error('Bluetooth device scan failed:', error);
        }
    }

    // Connect to device
    async connectDevice(deviceId) {
        const device = this.devices.find(d => d.id === deviceId);
        if (!device) {
            console.error('Device not found:', deviceId);
            return false;
        }
        
        try {
            if (device.type === 'hid') {
                await device.device.open();
                this.connectedDevices.set(deviceId, device);
                return true;
            }
            
            return true;
        } catch (error) {
            console.error('Failed to connect to device:', error);
            return false;
        }
    }

    // Disconnect device
    async disconnectDevice(deviceId) {
        const device = this.connectedDevices.get(deviceId);
        if (!device) return;
        
        try {
            if (device.type === 'hid') {
                await device.device.close();
            }
            
            this.connectedDevices.delete(deviceId);
        } catch (error) {
            console.error('Failed to disconnect device:', error);
        }
    }

    // Haptic feedback
    vibrate(duration, intensity = 1, pattern = []) {
        // Use Vibration API
        if (this.vibrationSupported) {
            if (pattern.length > 0) {
                navigator.vibrate(pattern);
            } else {
                navigator.vibrate(duration);
            }
        }
        
        // Also send to connected devices
        for (const [deviceId, device] of this.connectedDevices) {
            if (device.type === 'gamepad' && device.hasRumble) {
                device.vibrationActuator.playEffect('dual-rumble', {
                    startDelay: 0,
                    duration: duration,
                    weakMagnitude: intensity * 0.5,
                    strongMagnitude: intensity
                });
            }
        }
    }

    // Specific haptic patterns
    hapticClick() {
        this.vibrate(10, 0.5);
    }

    hapticHover() {
        this.vibrate(5, 0.3);
    }

    hapticTouch(intensity = 1) {
        this.vibrate(50, intensity);
    }

    hapticNotification() {
        this.vibrate([100, 50, 100]);
    }

    hapticPattern(pattern) {
        // Custom haptic pattern
        const vibrationPattern = [];
        
        for (const item of pattern) {
            vibrationPattern.push(item.duration);
            vibrationPattern.push(item.pause || 0);
        }
        
        this.vibrate(vibrationPattern);
    }

    // Body part-specific haptic feedback
    hapticBodyPart(bodyPart, intensity = 1) {
        const patterns = {
            'head': { duration: 30, intensity: intensity * 0.8 },
            'face': { duration: 25, intensity: intensity * 0.6 },
            'chest': { duration: 40, intensity: intensity * 1.0 },
            'hand': { duration: 20, intensity: intensity * 0.7 },
            'arm': { duration: 35, intensity: intensity * 0.9 }
        };
        
        const pattern = patterns[bodyPart] || patterns['hand'];
        this.vibrate(pattern.duration, pattern.intensity);
    }

    // Emotion-based haptic feedback
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

    // Get device info
    getDevice(deviceId) {
        return this.devices.find(d => d.id === deviceId);
    }

    getAllDevices() {
        return [...this.devices];
    }

    getConnectedDevices() {
        return Array.from(this.connectedDevices.values());
    }

    // Enable/disable
    enable() {
        this.isEnabled = true;
    }

    disable() {
        this.isEnabled = false;
    }

    shutdown() {
        // Disconnect all devices
        for (const [deviceId] of this.connectedDevices) {
            this.disconnectDevice(deviceId);
        }
        
        this.devices = [];
        this.connectedDevices.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HapticHandler;
}
