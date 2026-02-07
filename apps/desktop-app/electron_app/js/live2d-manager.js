/**
 * Angela AI - Live2D Manager (with Cubism SDK)
 * 
 * Live2D model manager with official Cubism Web SDK integration
 */

class Live2DManager {
    constructor(canvas) {
        this.canvas = canvas;
        this.gl = null;
        this.wrapper = null;
        
        this.modelLoaded = false;
        this.currentModel = null;
        this.modelPath = null;
        
        // Model state
        this.isRunning = false;
        this.lastFrameTime = 0;
        this.targetFPS = 60;
        this.currentFPS = 0;
        this.fpsHistory = [];
        
        // State
        this.currentExpression = 'neutral';
        this.currentMotion = 'idle';
        
        // Settings
        this.resolutionScale = 1.0;
        this.advancedAnimations = true;
        this.physicsEnabled = true;
        this.lipSyncEnabled = true;
        this.effectsLevel = 2;
        this.autoBlinkEnabled = true;
        this.autoBreathingEnabled = true;
        this.eyeTrackingEnabled = true;
        
        // Live2D parameters
        this.parameters = this._getDefaultParameters();
        this.parameterWeights = {
            energy: 1.0,
            comfort: 1.0,
            arousal: 0.5,
            rest_need: 0.5,
            vitality: 0.5,
            tension: 0.0
        };
        
        // Expressions (mapped from backend StateMatrix γ dimension)
        this.expressions = {
            neutral: {
                ParamEyeLOpen: 1,
                ParamEyeROpen: 1,
                ParamMouthForm: 0,
                ParamMouthOpenY: 0,
                ParamBrowLY: 0,
                ParamBrowRY: 0,
                ParamBrowLAngle: 0,
                ParamBrowRAngle: 0,
                ParamCheek: 0
            },
            happy: {
                ParamEyeLOpen: 0.8,
                ParamEyeROpen: 0.8,
                ParamEyeLSmile: 1,
                ParamEyeRSmile: 1,
                ParamMouthForm: 0.5,
                ParamMouthOpenY: 0.3,
                ParamBrowLY: 0.3,
                ParamBrowRY: 0.3,
                ParamCheek: 0.5
            },
            sad: {
                ParamEyeLOpen: 0.6,
                ParamEyeROpen: 0.6,
                ParamEyeLSmile: 0,
                ParamEyeRSmile: 0,
                ParamMouthForm: -0.3,
                ParamMouthOpenY: 0.2,
                ParamBrowLY: -0.2,
                ParamBrowRY: -0.2,
                ParamBrowLAngle: 0.2,
                ParamBrowRAngle: 0.2
            },
            angry: {
                ParamEyeLOpen: 0.7,
                ParamEyeROpen: 0.7,
                ParamEyeLSmile: 0,
                ParamEyeRSmile: 0,
                ParamMouthForm: -0.4,
                ParamMouthOpenY: 0.4,
                ParamBrowLY: 0.1,
                ParamBrowRY: 0.1,
                ParamBrowLAngle: -0.1,
                ParamBrowRAngle: -0.1
            },
            surprised: {
                ParamEyeLOpen: 1,
                ParamEyeROpen: 1,
                ParamEyeLSmile: 0,
                ParamEyeRSmile: 0,
                ParamMouthForm: -0.2,
                ParamMouthOpenY: 0.8,
                ParamBrowLY: 0.2,
                ParamBrowRY: 0.2,
                ParamCheek: 0
            },
            shy: {
                ParamEyeLOpen: 0.7,
                ParamEyeROpen: 0.7,
                ParamEyeLSmile: 0.3,
                ParamEyeRSmile: 0.3,
                ParamMouthForm: 0.2,
                ParamMouthOpenY: 0.1,
                ParamBrowLY: 0.1,
                ParamBrowRY: 0.1,
                ParamBrowLAngle: -0.05,
                ParamBrowRAngle: -0.05,
                ParamCheek: 0.5
            },
            love: {
                ParamEyeLOpen: 0.8,
                ParamEyeROpen: 0.8,
                ParamEyeLSmile: 1,
                ParamEyeRSmile: 1,
                ParamMouthForm: 0.3,
                ParamMouthOpenY: 0.25,
                ParamBrowLY: 0.2,
                ParamBrowRY: 0.2,
                ParamBrowLAngle: 0.1,
                ParamBrowRAngle: 0.1,
                ParamCheek: 0.8
            },
            calm: {
                ParamEyeLOpen: 1,
                ParamEyeROpen: 1,
                ParamEyeLSmile: 0,
                ParamEyeRSmile: 0,
                ParamMouthForm: 0,
                ParamMouthOpenY: 0,
                ParamBrowLY: 0,
                ParamBrowRY: 0,
                ParamBrowLAngle: 0,
                ParamBrowRAngle: 0,
                ParamCheek: 0
            }
        };
        
        // Motions (mapped from backend MaturitySystem capabilities)
        this.motions = {
            idle: { group: 'Scene1', name: 'Scene1' },
            greeting: { group: 'Scene2', name: 'Scene2' },
            thinking: { group: 'Scene2', name: 'Scene3' },
            dancing: { group: 'Scene3', name: 'Scene3' },
            waving: { group: 'Scene2', name: 'Scene1' },
            clapping: { group: 'Scene3', name: 'Scene2' },
            nod: { group: 'Scene2', name: 'Scene3' },
            shake: { group: 'Scene3', name: 'Scene2' }
        };
        
        // Clickable regions (mapped from BODY_TO_LIVE2D_MAPPING)
        this.clickableRegions = this._getClickableRegions();
        
        // Callbacks
        this.onClick = null;
        this.onDrag = null;
        this.onHover = null;
        this.onExpressionChanged = null;
        this.onMotionStarted = null;
        onMotionFinished = null;
        this.onError = null;
        
        // Initialize
        this._init();
    }
    
    _init() {
        console.log('Live2DManager initializing...');
        
        // Try to load SDK
        this._tryLoadSDK();
    }
    
    _tryLoadSDK() {
        if (typeof window.Live2DCubismCore !== 'undefined') {
            console.log('Live2D Cubism Core already loaded from CDN');
            this._initializeWithSDK(window.Live2DCubismCore);
        } else {
            console.log('Live2D Cubism Core not available, using fallback');
            this._createFallbackManager();
        }
    }
    
    _initializeWithSDK(CubismCore) {
        console.log('Initializing with Live2D Cubism Core');
        
        this.sdk = CubismCore;
        this.cubismSdk = CubismCore;
        
        this.gl = this.canvas.getContext('webgl2') || this.canvas.getContext('webgl');
        
        if (!this.gl) {
            console.error('WebGL not supported');
            return false;
        }

        // Initialize wrapper
        if (typeof Live2DCubismWrapper !== 'undefined') {
            this.wrapper = new Live2DCubismWrapper(this.canvas);
        } else {
            console.error('Live2DCubismWrapper not found');
            return false;
        }
        
        // Get WebGL extensions
        const ext = this.gl.getExtension('OES_element_index_uint');
        const ext2 = this.gl.getExtension('OES_standard_derivatives');
        const ext3 = this.gl.getExtension('OES_texture_float_linear');
        const ext4 = this.gl.getExtension('OES_texture_float');
        
        if (!ext || !ext2 || !ext3 || !ext4) {
            console.error('Required WebGL extensions not supported');
            return false;
        }
        
        console.log('WebGL extensions initialized');
        return true;
    }
    
    _createFallbackManager() {
        console.log('Creating fallback Live2D manager');
        
        this.sdk = null;
        this.model = null;
        this.modelLoaded = false;
        
        console.log('Fallback manager created (limited functionality)');
    }
    
    async initialize() {
        console.log('Initializing Live2D Manager...');
        
        return new Promise(async (resolve) => {
            let isResolved = false;
            const timeoutId = setTimeout(() => {
                if (!isResolved) {
                    isResolved = true;
                    console.error('Live2D Manager initialization timed out');
                    resolve(false);
                }
            }, 10000); // 10s timeout for SDK loading

            try {
                if (this.sdk && this.cubismSdk) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    resolve(true);
                    return;
                }
                
                if (!this.sdk) {
                    await this._tryLoadSDK();
                }
                
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    resolve(!!this.sdk);
                }
            } catch (error) {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    console.error('Live2D Manager initialization failed:', error);
                    resolve(false);
                }
            }
        });
    }
    
    async loadModel(modelPath) {
        console.log('Loading Live2D model from:', modelPath);
        
        if (!this.sdk || !this.wrapper) {
            console.error('Live2D Cubism SDK or Wrapper not loaded');
            return false;
        }
        
        return new Promise(async (resolve) => {
            let isResolved = false;
            const timeoutId = setTimeout(() => {
                if (!isResolved) {
                    isResolved = true;
                    console.error(`Live2D model loading timed out: ${modelPath}`);
                    resolve(false);
                }
            }, 15000); // 15s timeout for model loading

            try {
                const success = await this.wrapper.loadModel({
                    modelPath: modelPath
                });
                
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    
                    if (success) {
                        this.currentModelPath = modelPath;
                        this.currentModel = this.getModelName(modelPath);
                        this.modelLoaded = true;
                        
                        this.startAnimation();
                        
                        console.log('Live2D model loaded successfully:', this.currentModel);
                        resolve(true);
                    } else {
                        resolve(false);
                    }
                }
            } catch (error) {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    console.error('Failed to load Live2D model:', error);
                    resolve(false);
                }
            }
        });
    }
    
    getModelName(modelPath) {
        if (!modelPath) return 'unknown';
        
        const parts = modelPath.split(/[/\\]/);
        const folderName = parts[parts.length - 2] || parts[parts.length - 1];
        return folderName.replace(/[^a-zA-Z0-9]/g, '_');
    }
    
    startAnimation() {
        if (this.sdk && this.wrapper && !this.isRunning) {
            this.wrapper.start();
            this.isRunning = true;
            this.lastFrameTime = performance.now();
            this._startAnimationLoop();
        }
    }
    
    stopAnimation() {
        if (this.sdk && this.wrapper && this.isRunning) {
            this.wrapper.stop();
            this.isRunning = false;
            
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
                this.animationFrameId = null;
            }
        }
    }
    
    _startAnimationLoop() {
        const animate = () => {
            this.render();
            this.animationFrameId = requestAnimationFrame(animate);
            
            const now = performance.now();
            this.updateFPS(now);
        };
        
        this.animationFrameId = requestAnimationFrame(animate);
    }
    
    updateFPS(now) {
        const deltaTime = (now - this.lastFrameTime) || 16;
        this.lastFrameTime = now;
        
        const currentFPS = 1000 / deltaTime;
        this.fpsHistory.push(currentFPS);
        
        if (this.fpsHistory.length > 60) {
            this.fpsHistory.shift();
        }
        
        if (this.fpsHistory.length > 0) {
            this.currentFPS = this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length;
        }
    }
    
    render() {
        if (!this.sdk || !this.wrapper || !this.wrapper.isLoaded) {
            return;
        }
        
        this.wrapper.render();
        this.updateAnimations();
    }
    
    updateAnimations() {
        // Handle breathing
        if (this.autoBreathingEnabled) {
            const time = performance.now() / 1000;
            const breath = (Math.sin(time * 2) + 1) / 2;
            this.setParameter('ParamBreath', breath);
        }
        
        // Handle auto blink
        if (this.autoBlinkEnabled && !this.currentMotion || this.currentMotion === 'idle') {
            const time = performance.now() / 1000;
            const blinkSpeed = 0.125;
            const blinkPhase = (time * blinkSpeed) % 1;
            
            if (blinkPhase < 0.2 || blinkPhase > 0.8) {
                this.setParameter('ParamEyeLOpen', 0);
                this.setParameter('ParamEyeROpen', 0);
            }
        }
        
        // Handle eye tracking
        if (this.eyeTrackingEnabled && this.inputHandler) {
            const mousePos = this.inputHandler.getMousePosition();
            const canvasWidth = this.canvas.width || window.innerWidth;
            const canvasHeight = this.canvas.height || window.innerHeight;
            
            if (mousePos) {
                const eyeX = (mousePos.x / canvasWidth) * 2 - 1;
                const eyeY = (mousePos.y / canvasHeight) * 2 - 1;
                
                this.setParameter('ParamEyeBallX', eyeX);
                this.setParameter('ParamEyeBallY', eyeY);
            }
        }
    }
    
    setExpression(expression) {
        if (!this.modelLoaded) {
            return;
        }
        
        const newExpression = expression.trim().toLowerCase();
        
        if (!this.expressions[newExpression]) {
            console.warn(`Unknown expression: ${expression}`);
            return;
        }
        
        if (newExpression === this.currentExpression) {
            return;
        }
        
        this.currentExpression = newExpression;
        const params = this.expressions[newExpression];
        
        for (const [name, value] of Object.entries(params)) {
            this.setParameter(name, value);
        }
        
        if (this.onExpressionChanged) {
            this.onExpressionChanged(newExpression);
        }
    }
    
    resetPose() {
        if (!this.modelLoaded) {
            return;
        }
        
        const neutralParams = this.expressions['neutral'];
        
        for (const [name, value] of Object.entries(neutralParams)) {
            this.setParameter(name, value);
        }
        
        this.currentExpression = 'neutral';
        
        if (this.onExpressionChanged) {
            this.onExpressionChanged('neutral');
        }
    }
    
    async playMotion(groupName, motionName) {
        if (!this.modelLoaded) {
            return false;
        }
        
        const motion = this.motions[motionName];
        
        if (!motion) {
            console.warn(`Unknown motion: ${motionName}`);
            return false;
        }
        
        console.log(`Playing motion: ${motion.groupName}/${motion.name}`);
        
        try {
            const success = await this.wrapper.playMotion(motion.group, motion.name);
            
            if (success) {
                this.currentMotion = motionName;
                
                if (this.onMotionStarted) {
                    this.onMotionStarted(motionName);
                }
            }
        } catch (error) {
            console.error('Failed to play motion:', error);
        }
        
        return false;
    }
    
    stopAllMotions() {
        if (this.modelLoaded && this.sdk) {
            try {
                this.wrapper.stopMotion();
                this.currentMotion = 'idle';
                
                if (this.onMotionFinished) {
                    this.onMotionFinished(this.currentMotion);
                }
            } catch (error) {
                console.error('Failed to stop motions:', error);
            }
        }
    }
    
    enableLipSync(enabled) {
        this.lipSyncEnabled = enabled;
    }
    
    getParameters() {
        return this.parameters;
    }
    
    setParameter(name, value) {
        if (!this.modelLoaded) {
            return;
        }
        
        this.parameters[name] = value;
        
        if (this.sdk && this.wrapper) {
            this.wrapper.setParameter(name, value);
        }
    }
    
    setResolutionScale(scale) {
        this.resolutionScale = Math.max(0.5, Math.min(2.0, scale));
        
        if (this.wrapper) {
            this.wrapper.resize(
                Math.floor(this.canvas.width * scale),
                Math.floor(this.canvas.height * scale)
            );
        }
    }
    
    setEffectsLevel(level) {
        this.effectsLevel = Math.max(0, Math.min(4, level));
        
        if (!this.advancedAnimations && level > 1) {
            this.advancedAnimations = false;
        }
        
        this.updateAdvancedAnimations();
    }
    
    setAdvancedAnimations(enabled) {
        this.advancedAnimations = enabled;
        this.updateAdvancedAnimations();
    }
    
    updateAdvancedAnimations() {
        if (this.wrapper) {
            // Physics depends on advanced animations
            this.wrapper.setPhysicsEnabled(this.advancedAnimations && this.physicsEnabled);
        }
    }
    
    setPhysicsEnabled(enabled) {
        this.physicsEnabled = enabled;
        this.updateAdvancedAnimations();
    }
    
    setTargetFPS(fps) {
        this.targetFPS = Math.max(30, Math.min(120, fps));
        
        if (this.wrapper) {
            this.wrapper.setTargetFPS(fps);
        }
    }
    
    getCurrentFPS() {
        return this.currentFPS;
    }
    
    _getDefaultParameters() {
        return {
            // Face angles
            ParamAngleX: 0,
            ParamAngleY: 0,
            ParamAngleZ: 0,
            
            // Eyes
            ParamEyeLOpen: 1,
            ParamEyeROpen: 1,
            ParamEyeLSmile: 0,
            ParamEyeRSmile: 0,
            ParamEyeBallX: 0,
            ParamEyeBallY: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            ParamEyeBlink: 0,
            
            // Eyebrows
            ParamBrowLY: 0,
            ParamBrowRY: 0,
            ParamBrowLAngle: 0,
            ParamBrowRAngle: 0,
            
            // Mouth
            ParamMouthForm: 0,
            ParamMouthOpenY: 0,
            
            // Body
            ParamBodyAngleX: 0,
            ParamBodyAngleY: 0,
            ParamBodyAngleZ: 0,
            
            // Hair
            ParamHairFront: 0,
            ParamHairSide: 0,
            ParamHairBack: 0,
            
            // Arms
            ParamArmLA: 0,
            ParamArmRA: 0,
            ParamArmLA: 0,
            ParamArmRA: 0,
            
            // Other
            ParamBreath: 0.5,
            ParamAllDelete: false,
            ParamRandom: false
        };
    }
    
    _getClickableRegions() {
        return [
            { name: 'head', x: 0.5, y: 0.15, width: 0.3, height: 0.25 },
            { name: 'face', x: 0.5, y: 0.2, width: 0.2, height: 0.2 },
            { name: 'chest', x: 0.5, y: 0.55, width: 0.2, height: 0.15 },
            { name: 'left_arm', x: 0.25, y: 0.55, width: 0.2, height: 0.4 },
            { name: 'right_arm', x: 0.75, y: 0.55, width: 0.2, height: 0.4 }
        ];
    }
    
    getClickableRegions() {
        return this.clickableRegions;
    }
    
    getInputHandler(handler) {
        this.inputHandler = handler;
    }
    
    shutdown() {
        console.log('Shutting down Live2D Manager...');
        
        this.stopAnimation();
        
        if (this.wrapper) {
            this.wrapper.destroy();
        }
        
        this.sdk = null;
        this.modelLoaded = false;
        this.isRunning = false;
        this.currentModel = null;
        
        console.log('Live2D Manager shutdown complete');
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DManager;
}