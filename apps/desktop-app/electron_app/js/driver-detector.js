/**
 * Angela AI - Driver Detector
 * 
 * Detects and monitors system drivers for optimal performance
 * Supports: GPU, Audio, Input, Network drivers
 */

class DriverDetector {
    constructor() {
        this.driverCache = new Map();
        this.driverStatus = {
            gpu: { name: null, version: null, date: null, status: 'unknown' },
            audio: { name: null, version: null, date: null, status: 'unknown' },
            input: { name: null, version: null, date: null, status: 'unknown' },
            network: { name: null, version: null, date: null, status: 'unknown' }
        };
        this.lastUpdate = null;
        this.isInitialized = false;
    }

    /**
     * Initialize driver detection
     */
    async initialize() {
        console.log('[DriverDetector] Initializing driver detection...');
        
        try {
            // Detect GPU driver
            await this._detectGPUDriver();
            
            // Detect audio driver
            await this._detectAudioDriver();
            
            // Detect input drivers
            await this._detectInputDriver();
            
            // Detect network driver
            await this._detectNetworkDriver();
            
            this.isInitialized = true;
            this.lastUpdate = new Date();
            console.log('[DriverDetector] Driver detection initialized');
            
            return this.getDriverStatus();
        } catch (error) {
            console.error('[DriverDetector] Initialization error:', error);
            return this.getDriverStatus();
        }
    }

    /**
     * Detect GPU driver
     */
    async _detectGPUDriver() {
        console.log('[DriverDetector] Detecting GPU driver...');
        
        try {
            // Try WebGL info first
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            
            if (gl) {
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                    
                    this.driverStatus.gpu = {
                        name: vendor,
                        version: this._extractDriverVersion(renderer),
                        renderer: renderer,
                        date: null, // Cannot get date from WebGL
                        status: 'active',
                        memory: gl.getParameter(gl.GPU_MEMORY_INFO_TOTAL_AVAILABLE_MEMORY_NVX) || 'unknown',
                        api: gl.getParameter(gl.VERSION)
                    };
                    
                    console.log('[DriverDetector] GPU:', this.driverStatus.gpu);
                    return;
                }
            }
            
            // Fallback: Try to read from /proc on Linux
            await this._detectGPUFromSystem();
            
        } catch (error) {
            console.warn('[DriverDetector] GPU detection error:', error);
            this.driverStatus.gpu.status = 'error';
        }
    }

    /**
     * Detect GPU from Linux system files
     */
    async _detectGPUFromSystem() {
        try {
            // Check lspci for GPU info
            const gpuInfo = await this._runCommand('lspci -vnn 2>/dev/null | grep -i -A5 vga');
            
            if (gpuInfo) {
                const lines = gpuInfo.split('\n');
                const driverMatch = gpuInfo.match(/Kernel driver in use:\s+(\S+)/);
                const moduleMatch = gpuInfo.match(/Kernel modules:\s+(\S+)/);
                
                this.driverStatus.gpu = {
                    name: lines[0]?.trim() || 'Unknown GPU',
                    version: driverMatch?.[1] || moduleMatch?.[1] || 'unknown',
                    date: null,
                    status: 'active',
                    rawInfo: gpuInfo
                };
            }
            
        } catch (error) {
            console.warn('[DriverDetector] System GPU detection failed:', error);
        }
    }

    /**
     * Detect audio driver
     */
    async _detectAudioDriver() {
        console.log('[DriverDetector] Detecting audio driver...');
        
        try {
            // Try ALSA info
            const audioInfo = await this._runCommand('aplay -l 2>/dev/null || cat /proc/asound/cards 2>/dev/null');
            
            if (audioInfo) {
                const cards = audioInfo.split('\n').filter(line => line.includes('card'));
                this.driverStatus.audio = {
                    name: cards[0]?.match(/card \d+:\s+(.+?)(?:\[|$)/)?.[1] || 'Unknown Audio',
                    version: this._detectALSAVersion(),
                    date: null,
                    status: cards.length > 0 ? 'active' : 'not_found',
                    devices: cards.length
                };
            } else {
                // Check for PulseAudio
                const pulseInfo = await this._runCommand('pulseaudio --version 2>/dev/null');
                if (pulseInfo) {
                    this.driverStatus.audio = {
                        name: 'PulseAudio',
                        version: pulseInfo.trim(),
                        date: null,
                        status: 'active'
                    };
                }
            }
            
        } catch (error) {
            console.warn('[DriverDetector] Audio detection error:', error);
            this.driverStatus.audio.status = 'error';
        }
    }

    /**
     * Detect ALSA version
     */
    _detectALSAVersion() {
        try {
            const version = this._runCommand('cat /proc/asound/version 2>/dev/null');
            return version?.match(/Version (\S+)/)?.[1] || 'unknown';
        } catch {
            return 'unknown';
        }
    }

    /**
     * Detect input drivers
     */
    async _detectInputDriver() {
        console.log('[DriverDetector] Detecting input drivers...');
        
        try {
            // Check input devices
            const inputInfo = await this._runCommand('cat /proc/bus/input/devices 2>/dev/null');
            
            if (inputInfo) {
                const devices = inputInfo.split('\n\n').length - 1;
                const handlers = inputInfo.match(/H: Handlers=(\S+)/g) || [];
                
                this.driverStatus.input = {
                    name: 'Linux Input System',
                    version: this._getKernelVersion(),
                    date: null,
                    status: devices > 0 ? 'active' : 'not_found',
                    devices: devices,
                    handlers: handlers.map(h => h.replace('H: Handlers=', ''))
                };
            }
            
        } catch (error) {
            console.warn('[DriverDetector] Input detection error:', error);
            this.driverStatus.input.status = 'error';
        }
    }

    /**
     * Detect network driver
     */
    async _detectNetworkDriver() {
        console.log('[DriverDetector] Detecting network driver...');
        
        try {
            const networkInfo = await this._runCommand('lsmod 2>/dev/null | grep -E "e1000|rtl|ath|iwl" | head -5');
            
            if (networkInfo) {
                const modules = networkInfo.split('\n').filter(m => m.trim());
                this.driverStatus.network = {
                    name: modules[0]?.split(' ')[0] || 'Unknown Network',
                    version: this._getKernelVersion(),
                    date: null,
                    status: 'active',
                    modules: modules
                };
            } else {
                this.driverStatus.network.status = 'not_found';
            }
            
        } catch (error) {
            console.warn('[DriverDetector] Network detection error:', error);
            this.driverStatus.network.status = 'error';
        }
    }

    /**
     * Run system command
     */
    async _runCommand(cmd) {
        try {
            // This would use Electron's ipcRenderer to run commands
            if (window.electronAPI?.shell) {
                const result = await window.electronAPI.shell.executeCommand(cmd);
                return result.stdout || result;
            }
            return null;
        } catch {
            return null;
        }
    }

    /**
     * Get kernel version
     */
    _getKernelVersion() {
        return navigator.userAgent?.match(/Linux (\S+)/)?.[1] || 'unknown';
    }

    /**
     * Extract driver version from renderer string
     */
    _extractDriverVersion(renderer) {
        if (!renderer) return 'unknown';
        
        // Try to extract version from common patterns
        const patterns = [
            /(\d+\.\d+\.\d+\.\d+)/,  // X.X.X.X
            /(\d+\.\d+)/,             // X.X
            /clang (\d+)/,            // clang
            / Mesa (\d+)/              // Mesa
        ];
        
        for (const pattern of patterns) {
            const match = renderer.match(pattern);
            if (match) return match[1];
        }
        
        return 'unknown';
    }

    /**
     * Check for driver updates
     */
    async checkForUpdates() {
        console.log('[DriverDetector] Checking for driver updates...');
        
        const updates = {
            gpu: null,
            audio: null,
            input: null,
            network: null
        };
        
        // In a real implementation, this would check:
        // - NVIDIA website for GPU updates
        // - AMD website for GPU updates
        // - System package manager for driver packages
        
        // For now, provide check commands
        updates.gpu = {
            available: false,
            checkCommand: 'apt list --upgradable 2>/dev/null | grep -E "nvidia|mesa|xf86-video"',
            updateCommand: 'sudo apt update && sudo apt upgrade'
        };
        
        updates.audio = {
            available: false,
            checkCommand: 'apt list --upgradable 2>/dev/null | grep -E "alsa|pulseaudio"',
            updateCommand: 'sudo apt update && sudo apt upgrade'
        };
        
        this.driverStatus.updates = updates;
        return updates;
    }

    /**
     * Get comprehensive driver status
     */
    getDriverStatus() {
        return {
            ...this.driverStatus,
            lastUpdate: this.lastUpdate,
            isInitialized: this.isInitialized,
            overallHealth: this._calculateHealth()
        };
    }

    /**
     * Calculate overall driver health
     */
    _calculateHealth() {
        const statuses = Object.values(this.driverStatus)
            .filter(d => typeof d === 'object' && d.status)
            .map(d => d.status);
        
        if (statuses.includes('error')) return 'critical';
        if (statuses.includes('not_found')) return 'warning';
        if (statuses.every(s => s === 'active')) return 'healthy';
        return 'degraded';
    }

    /**
     * Run diagnostic test
     */
    async runDiagnostics() {
        console.log('[DriverDetector] Running diagnostics...');
        
        const results = {
            timestamp: new Date(),
            tests: [],
            score: 0,
            maxScore: 100
        };
        
        // Test GPU
        const gpuTest = await this._testGPU();
        results.tests.push(gpuTest);
        
        // Test Audio
        const audioTest = await this._testAudio();
        results.tests.push(audioTest);
        
        // Test Input
        const inputTest = await this._testInput();
        results.tests.push(inputTest);
        
        // Calculate score
        const passed = results.tests.filter(t => t.passed).length;
        results.score = Math.round((passed / results.tests.length) * 100);
        
        console.log('[DriverDetector] Diagnostics score:', results.score);
        return results;
    }

    /**
     * Test GPU functionality
     */
    async _testGPU() {
        const result = {
            name: 'GPU Driver',
            passed: false,
            details: {}
        };
        
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl2');
            
            if (gl) {
                result.passed = true;
                result.details = {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    version: gl.getParameter(gl.VERSION),
                    extensions: gl.getSupportedExtensions()?.length || 0
                };
            } else {
                result.details.error = 'WebGL not supported';
            }
        } catch (error) {
            result.details.error = error.message;
        }
        
        return result;
    }

    /**
     * Test Audio functionality
     */
    async _testAudio() {
        const result = {
            name: 'Audio Driver',
            passed: false,
            details: {}
        };
        
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            result.passed = audioContext.state === 'running';
            result.details = {
                state: audioContext.state,
                sampleRate: audioContext.sampleRate,
                channels: audioContext.destination.maxChannelCount
            };
            audioContext.close();
        } catch (error) {
            result.details.error = error.message;
        }
        
        return result;
    }

    /**
     * Test Input functionality
     */
    async _testInput() {
        const result = {
            name: 'Input Driver',
            passed: false,
            details: {}
        };
        
        try {
            // Test pointer events
            const hasPointerEvents = window.PointerEvent !== undefined;
            const hasTouch = 'ontouchstart' in window;
            
            result.passed = hasPointerEvents;
            result.details = {
                pointerEvents: hasPointerEvents,
                touchSupport: hasTouch,
                mousePresent: window.matchMedia('(pointer: fine)').matches
            };
        } catch (error) {
            result.details.error = error.message;
        }
        
        return result;
    }

    /**
     * Generate driver report
     */
    generateReport() {
        return {
            title: 'Angela AI - Driver Detection Report',
            generatedAt: new Date().toISOString(),
            system: {
                platform: navigator.platform,
                userAgent: navigator.userAgent,
                language: navigator.language
            },
            drivers: this.driverStatus,
            health: this._calculateHealth(),
            recommendations: this._generateRecommendations()
        };
    }

    /**
     * Generate recommendations based on driver status
     */
    _generateRecommendations() {
        const recommendations = [];
        
        if (this.driverStatus.gpu.status === 'error') {
            recommendations.push({
                priority: 'high',
                message: 'GPU driver issue detected. Consider updating graphics drivers.',
                action: 'Check NVIDIA/AMD driver updates'
            });
        }
        
        if (this.driverStatus.audio.status === 'not_found') {
            recommendations.push({
                priority: 'medium',
                message: 'Audio driver not detected. Sound features may be limited.',
                action: 'Install ALSA or PulseAudio drivers'
            });
        }
        
        return recommendations;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DriverDetector;
}
