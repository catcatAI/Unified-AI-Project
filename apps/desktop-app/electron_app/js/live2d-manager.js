/**
 * Angela AI - Live2D Manager (with Cubism SDK)
 * 
 * Live2D model manager with official Cubism Web SDK integration
 */

class Live2DManager {
    constructor(canvas) {
        console.log('[Live2DManager] Constructor called with canvas:', canvas);
        
        this.canvas = canvas;
        this.gl = null;
        this.wrapper = null;
        this.isFramework = false;
        this.frameworkLoaded = false;
        
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
        this.onMotionFinished = null;
        this.onError = null;
        
        // Initialize
        this._init();
    }
    
    _init() {
        console.log('[Live2DManager] _init called');
        
        // Try to load SDK
        this._tryLoadSDK();
    }
    
    _tryLoadSDK() {
        console.log('[Live2DManager] _tryLoadSDK called');
        console.log('[Live2DManager] Checking window.Live2DCubismCore:', typeof window.Live2DCubismCore);
        console.log('[Live2DManager] Checking window.Live2DCubismFramework:', typeof window.Live2DCubismFramework);
        console.log('[Live2DManager] Checking window.Live2DCubismWrapper:', typeof window.Live2DCubismWrapper);
        
        // Check for Core SDK (required)
        if (typeof window.Live2DCubismCore !== 'undefined') {
            console.log('Live2D Cubism Core loaded');
            
            // Check for Framework SDK (SDK 5)
            if (typeof window.Live2DCubismFramework !== 'undefined') {
                console.log('Live2D Cubism Framework loaded (SDK 5)');
                this.frameworkLoaded = true;
            }
            
            // Initialize SDK and check return value
            const initResult = this._initializeWithSDK(window.Live2DCubismCore);
            if (!initResult) {
                console.log('SDK initialization failed, fallback will be used');
            }
        } else {
            console.log('Live2D Cubism Core not available, using fallback');
            this._createFallbackManager();
        }
    }
    
    _initializeWithSDK(CubismCore) {
        console.log('Initializing with Live2D Cubism SDK');
        console.log('CubismCore type:', typeof CubismCore);
        
        // Validate Core SDK structure
        if (!CubismCore || typeof CubismCore !== 'object') {
            console.error('Invalid CubismCore SDK - not an object');
            this._createFallbackManager();
            return false;
        }
        
        // Check for Core SDK functions (SDK 5 format)
        const hasCoreSDK = typeof CubismCore.Moc !== 'undefined' &&
                          typeof CubismCore.Memory !== 'undefined';
        console.log('Core SDK has Moc/Memory:', hasCoreSDK);
        
        // Check for Framework SDK (SDK 5) - bundle format
        let hasFramework = false;
        let CubismFramework = null;
        
        if (typeof window.Live2DCubismFramework !== 'undefined') {
            // Check for nested CubismFramework (bundle format)
            if (window.Live2DCubismFramework.CubismFramework) {
                hasFramework = true;
                CubismFramework = window.Live2DCubismFramework.CubismFramework;
                console.log('Framework SDK loaded (nested CubismFramework)');
            }
            // Or check for direct Framework access
            else if (typeof window.Live2DCubismFramework.startUp === 'function') {
                hasFramework = true;
                CubismFramework = window.Live2DCubismFramework;
                console.log('Framework SDK loaded (direct)');
            }
        }
        
        console.log('Framework SDK loaded:', hasFramework);
        
        // Check for wrapper (SDK 4 style)
        const hasWrapper = typeof window.Live2DCubismWrapper !== 'undefined';
        console.log('Wrapper SDK loaded:', hasWrapper);
        
        // SDK 5: Initialize Framework with Core
        if (hasFramework && hasCoreSDK && CubismFramework) {
            console.log('Using SDK 5 Framework + Core');

            // Check if Framework was already initialized
            const alreadyInitialized = window.Live2DCubismFramework?.initialized === true;
            if (!alreadyInitialized) {
                // Try to initialize via wrapper function first
                if (typeof window.initLive2DFramework === 'function') {
                    console.log('Calling window.initLive2DFramework()');
                    window.initLive2DFramework();
                }

                // Verify initialization
                if (window.Live2DCubismFramework?.initialized !== true) {
                    // Manual initialization if wrapper didn't work
                    try {
                        // Start up Framework
                        if (typeof CubismFramework.startUp === 'function') {
                            CubismFramework.startUp();
                            console.log('Framework.startUp() called');
                        }

                        // Initialize Framework
                        if (typeof CubismFramework.initialize === 'function') {
                            const memorySize = CubismCore.Memory?.getMemorySize?.() || (16 * 1024 * 1024);
                            CubismFramework.initialize(memorySize);
                            console.log('Framework.initialize() called with', memorySize, 'bytes');
                        }

                        // Mark as initialized
                        window.Live2DCubismFramework.initialized = true;
                    } catch (e) {
                        console.error('Framework initialization failed:', e);
                    }
                }
            }

            // Verify and set SDK references
            if (window.Live2DCubismFramework?.initialized === true || !alreadyInitialized) {
                this.sdk = CubismFramework;
                this.cubismSdk = window.Live2DCubismFramework;
                this.isFramework = true;
                console.log('SDK 5 initialization successful');
            } else {
                console.error('Framework initialization did not complete');
                this._createFallbackManager();
                return false;
            }
        }
        // SDK 4 wrapper fallback
        else if (hasWrapper && typeof window.Live2DCubismWrapper.initialize === 'function') {
            console.log('Using SDK 4 Wrapper');
            this.sdk = window.Live2DCubismWrapper;
            this.cubismSdk = window.Live2DCubismWrapper;
            window.Live2DCubismWrapper.initialize(CubismCore);
        }
        // Core SDK only (limited functionality)
        else if (hasCoreSDK) {
            console.log('Using Core SDK only (limited functionality)');
            this.sdk = CubismCore;
            this.cubismSdk = CubismCore;
        }
        else {
            console.warn('Live2D SDK incomplete, running in compatibility mode');
            console.log('hasCoreSDK:', hasCoreSDK, 'hasFramework:', hasFramework, 'hasWrapper:', hasWrapper);
            this._createFallbackManager();
            return false;
        }
        
        // Initialize canvas size using FrontendUtils for reliable DOM layout handling
        const initialSize = FrontendUtils.getElementSize(this.canvas, 800, 600);
        this.canvas.width = initialSize.width;
        this.canvas.height = initialSize.height;

        console.log('Canvas dimensions set to:', this.canvas.width, 'x', this.canvas.height);
        
        // Get WebGL context - try high-performance first for Live2D
        const glOptions = {
            alpha: false,
            antialias: true,
            preserveDrawingBuffer: true,
            powerPreference: 'high-performance',  // Changed from 'low-power' for Live2D
            desynchronized: true,
            failIfMajorPerformanceCaveat: false
        };

        this.gl = FrontendUtils.getWebGLContext(this.canvas, glOptions);

        if (!this.gl) {
            console.error('WebGL not supported with high-performance, trying default...');
            this.gl = FrontendUtils.getWebGLContext(this.canvas, {});
        }
        
        if (!this.gl) {
            console.error('WebGL not supported - Live2D requires WebGL');
            console.error('This may be due to transparent window or software rendering limitations');
            this._createFallbackManager();
            return false;
        }

        console.log('WebGL context created successfully');
        console.log('WebGL vendor:', this.gl.getParameter(this.gl.VENDOR));
        console.log('WebGL renderer:', this.gl.getParameter(this.gl.RENDERER));
        console.log('WebGL version:', this.gl.getParameter(this.gl.VERSION));
        
        // Try to enable required extensions manually
        this._enableWebGLExtensions();
        
        // Add WebGL context lost/restored event handlers
        this.canvas.addEventListener('webglcontextlost', (event) => {
            console.error('WebGL context lost!', event);
            event.preventDefault(); // Prevent the context from being deleted
            this._onContextLost();
        });
        
        this.canvas.addEventListener('webglcontextrestored', (event) => {
            console.log('WebGL context restored, reinitializing...');
            this._onContextRestored();
        });
        
        // Initialize based on SDK type
        // SDK 5 Framework mode
        if (this.isFramework && this.sdk) {
            console.log('Using SDK 5 Framework mode');
            this._setupLive2DLoop();
            return true;
        }
        // SDK 4 Wrapper mode
        else if (typeof Live2DCubismWrapper !== 'undefined') {
            console.log('Using SDK 4 Wrapper mode');
            this.wrapper = new Live2DCubismWrapper(this.canvas);
            this._setupLive2DLoop();
            return true;
        }
        // Enhanced wrapper fallback
        else if (typeof EnhancedLive2DCubismWrapper !== 'undefined') {
            console.log('Using Enhanced Wrapper mode');
            this.wrapper = new EnhancedLive2DCubismWrapper(this.canvas);
            this._setupLive2DLoop();
            return true;
        }
        // No SDK available
        else {
            console.error('No Live2D wrapper available');
            this._createFallbackManager();
            return false;
        }
    }
    
    /**
     * Enable WebGL extensions manually for Live2D
     */
    _enableWebGLExtensions() {
        if (!this.gl) return;
        
        const extensionsToEnable = [
            'OES_element_index_uint',
            'OES_texture_float',
            'OES_texture_float_linear',
            'OES_standard_derivatives',
            'WEBGL_depth_texture',
            'EXT_color_buffer_float',
            'EXT_texture_filter_anisotropic'
        ];
        
        console.log('Attempting to enable WebGL extensions...');
        const enabled = [];
        const failed = [];
        
        for (const ext of extensionsToEnable) {
            try {
                const extObj = this.gl.getExtension(ext);
                if (extObj) {
                    enabled.push(ext);
                    console.log('  ✅ Enabled:', ext);
                } else {
                    // Try enabling it
                    const extObj2 = this.gl.getExtension(ext);
                    if (extObj2) {
                        enabled.push(ext);
                        console.log('  ✅ Enabled (second try):', ext);
                    } else {
                        failed.push(ext);
                        console.warn('  ❌ Not available:', ext);
                    }
                }
            } catch (e) {
                failed.push(ext);
                console.warn('  ❌ Error:', ext, e.message);
            }
        }
        
        this.enabledExtensions = enabled;
        this.failedExtensions = failed;
        
        console.log(`WebGL Extensions: ${enabled.length} enabled, ${failed.length} failed`);
        
        // Check for critical Live2D requirements
        const hasElementIndexUint = enabled.includes('OES_element_index_uint');
        const hasTextureFloat = enabled.includes('OES_texture_float');
        
        if (!hasElementIndexUint || !hasTextureFloat) {
            console.warn('⚠️ Critical Live2D extensions missing - using fallback');
            this._createFallbackManager();
        }
    }
    
    /**
     * Set up the Live2D render loop
     */
    _setupLive2DLoop() {
        console.log('[Live2DManager] Setting up render loop');

        this.isRunning = true;
        this.lastFrameTime = performance.now();

        // Render loop using requestAnimationFrame
        const render = (timestamp) => {
            if (!this.isRunning) return;

            const deltaTime = timestamp - this.lastFrameTime;
            this.lastFrameTime = timestamp;

            try {
                if (this.isFramework && this.model) {
                    // SDK 5 Framework rendering
                    this._renderFramework();
                } else if (this.wrapper) {
                    // SDK 4 Wrapper rendering
                    this.wrapper.update(deltaTime);
                    this.wrapper.render();
                }
                // Fallback mode doesn't need render loop here - handled by _create2DFallbackCharacter
            } catch (e) {
                console.error('Render error:', e);
            }

            requestAnimationFrame(render);
        };

        requestAnimationFrame(render);
        console.log('[Live2DManager] Render loop started (mode:', this.isFallback ? 'fallback' : 'SDK', ')');
    }
    
    /**
     * Render using SDK 5 Framework
     */
    _renderFramework() {
        // Placeholder for SDK 5 rendering
        if (this.model) {
            // Model rendering would go here
        }
    }
    
    _createFallbackManager() {
        console.log('[Live2DManager] Creating enhanced fallback manager');
        
        // 設置 sdk 為空對象而不是 null，避免 initialize 循環調用
        this.sdk = {};  
        this.model = null;
        this.modelLoaded = false;
        this.isFallback = true;
        
        // Create 2D canvas fallback with animation
        this._create2DFallbackCharacter();
        
        console.log('[Live2DManager] Enhanced fallback manager created');
    }
    
    /**
     * Create an animated 2D fallback character that looks like Angela
     */
    _create2DFallbackCharacter() {
        console.log('[Live2DManager] _create2DFallbackCharacter called');

        // Use separate canvas for fallback (main canvas has WebGL context)
        const fallbackCanvas = document.getElementById('fallback-canvas');
        const ctx = fallbackCanvas.getContext('2d');

        if (!fallbackCanvas || !ctx) {
            console.error('[Live2DManager] Failed to get fallback canvas or 2D context');
            return;
        }

        // Show fallback canvas, hide WebGL canvas
        fallbackCanvas.style.display = 'block';
        this.canvas.style.display = 'none';

        // Set canvas size
        fallbackCanvas.width = 400;
        fallbackCanvas.height = 500;

        // Store reference
        this.fallbackCanvas = fallbackCanvas;
        this.fallbackCtx = ctx;

        console.log('[Live2DManager] Fallback canvas created:', fallbackCanvas.width, 'x', fallbackCanvas.height);
        
        // Character state
        this.fallbackState = {
            blinkTimer: 0,
            blinkInterval: 2000 + Math.random() * 2000,
            isBlinking: false,
            blinkDuration: 150,
            breathePhase: 0,
            breatheSpeed: 0.03,
            idlePhase: 0,
            idleSpeed: 0.02,
            mouseX: 0,
            mouseY: 0,
            eyeOffset: { x: 0, y: 0 },
            colorHue: 200,  // Blue-purple theme
            expression: 'neutral',
            hoverRegion: null
        };
        
        // Animation loop for fallback character
        const animate = () => {
            if (this.isFallback && this.fallbackCtx) {
                this._drawFallbackCharacter(this.fallbackCtx);
                this._updateFallbackState();
            }
            if (this.isFallback) {
                this.fallbackAnimationId = requestAnimationFrame(animate);
            }
        };

        // Start animation
        this._drawFallbackCharacter(ctx);
        this.fallbackAnimationId = requestAnimationFrame(animate);
        
        console.log('[Live2DManager] 2D fallback character animation started');
    }
    
    /**
     * Update fallback character state (blinking, breathing, idle motion)
     */
    _updateFallbackState() {
        if (!this.fallbackState) return;
        
        const state = this.fallbackState;
        const now = Date.now();
        
        // Update blink
        state.blinkTimer += 16;
        if (!state.isBlinking && state.blinkTimer >= state.blinkInterval) {
            state.isBlinking = true;
            state.blinkTimer = 0;
        }
        if (state.isBlinking && state.blinkTimer >= state.blinkDuration) {
            state.isBlinking = false;
            state.blinkTimer = 0;
        }
        
        // Update breathing
        state.breathePhase += state.breatheSpeed;
        
        // Update idle motion
        state.idlePhase += state.idleSpeed;
        
        // Smooth eye tracking towards mouse
        const targetEyeX = (state.mouseX - 0.5) * 15;
        const targetEyeY = (state.mouseY - 0.5) * 10;
        state.eyeOffset.x += (targetEyeX - state.eyeOffset.x) * 0.1;
        state.eyeOffset.y += (targetEyeY - state.eyeOffset.y) * 0.1;
    }
    
    /**
     * Draw the fallback character (Angela-style)
     */
    _drawFallbackCharacter(ctx) {
        if (!ctx || !this.fallbackState || !this.fallbackCanvas) return;

        const state = this.fallbackState;
        const w = this.fallbackCanvas.width;
        const h = this.fallbackCanvas.height;
        const cx = w / 2;
        const cy = h / 2 - 30;
        
        // Clear canvas
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, w, h);
        
        // Breathing offset
        const breatheOffset = Math.sin(state.breathePhase) * 3;
        const idleX = Math.sin(state.idlePhase * 0.7) * 5;
        const idleY = Math.sin(state.idlePhase * 0.5) * 3;
        
        // Draw character
        ctx.save();
        ctx.translate(cx + idleX, cy + idleY + breatheOffset);
        
        // Colors
        const skinColor = '#FFE4D0';
        const hairColor = '#4A90D9';
        const eyeColor = '#2E5A8B';
        const lipColor = '#E890A0';
        const blushColor = '#FFB6C1';
        const dressColor = '#6B8EB8';
        
        // Draw back hair
        ctx.fillStyle = hairColor;
        ctx.beginPath();
        ctx.ellipse(0, 40, 95, 110, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw body/dress
        ctx.fillStyle = dressColor;
        ctx.beginPath();
        ctx.moveTo(-60, 120);
        ctx.quadraticCurveTo(-80, 180, -70, 220);
        ctx.lineTo(70, 220);
        ctx.quadraticCurveTo(80, 180, 60, 120);
        ctx.fill();
        
        // Draw neck
        ctx.fillStyle = skinColor;
        ctx.fillRect(-15, 90, 30, 35);
        
        // Draw face (head)
        ctx.fillStyle = skinColor;
        ctx.beginPath();
        ctx.ellipse(0, 20, 75, 85, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw bangs/fringe
        ctx.fillStyle = hairColor;
        ctx.beginPath();
        ctx.moveTo(-70, -10);
        ctx.quadraticCurveTo(-40, 30, 0, 20);
        ctx.quadraticCurveTo(40, 30, 70, -10);
        ctx.quadraticCurveTo(50, -40, 0, -50);
        ctx.quadraticCurveTo(-50, -40, -70, -10);
        ctx.fill();
        
        // Draw side hair
        ctx.beginPath();
        ctx.moveTo(-75, 20);
        ctx.quadraticCurveTo(-100, 80, -90, 150);
        ctx.lineTo(-70, 150);
        ctx.quadraticCurveTo(-80, 80, -60, 30);
        ctx.fill();
        
        ctx.beginPath();
        ctx.moveTo(75, 20);
        ctx.quadraticCurveTo(100, 80, 90, 150);
        ctx.lineTo(70, 150);
        ctx.quadraticCurveTo(80, 80, 60, 30);
        ctx.fill();
        
        // Draw eyes (white part)
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.ellipse(-28, 15, 22, 18, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(28, 15, 22, 18, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw iris
        ctx.fillStyle = eyeColor;
        ctx.beginPath();
        const eyeX = state.eyeOffset.x;
        const eyeY = state.eyeOffset.y;
        ctx.ellipse(-28 + eyeX, 15 + eyeY, 12, 14, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(28 + eyeX, 15 + eyeY, 12, 14, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw pupils
        ctx.fillStyle = '#1a1a2e';
        ctx.beginPath();
        ctx.ellipse(-28 + eyeX * 1.2, 15 + eyeY * 1.2, 6, 7, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(28 + eyeX * 1.2, 15 + eyeY * 1.2, 6, 7, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw eye highlights
        ctx.fillStyle = '#FFFFFF';
        ctx.beginPath();
        ctx.ellipse(-32 + eyeX, 11 + eyeY, 4, 5, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(24 + eyeX, 11 + eyeY, 4, 5, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw eyebrows
        ctx.strokeStyle = hairColor;
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(-45, -5);
        ctx.quadraticCurveTo(-28, -12, -10, -5);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(45, -5);
        ctx.quadraticCurveTo(28, -12, 10, -5);
        ctx.stroke();
        
        // Draw nose
        ctx.strokeStyle = 'rgba(0,0,0,0.1)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, 30);
        ctx.quadraticCurveTo(5, 50, 0, 55);
        ctx.stroke();
        
        // Draw mouth
        ctx.fillStyle = lipColor;
        ctx.beginPath();
        ctx.moveTo(-15, 70);
        ctx.quadraticCurveTo(0, 78, 15, 70);
        ctx.quadraticCurveTo(0, 82, -15, 70);
        ctx.fill();
        
        // Draw blush
        ctx.fillStyle = blushColor + '88';
        ctx.beginPath();
        ctx.ellipse(-50, 45, 15, 10, -0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(50, 45, 15, 10, 0.2, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw cheeks highlight
        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.beginPath();
        ctx.ellipse(-55, 40, 8, 5, -0.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(55, 40, 8, 5, 0.2, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
        
        // Draw status indicator
        ctx.fillStyle = state.isBlinking ? '#FFB347' : '#4CAF50';
        ctx.font = '12px Arial';
        ctx.textAlign = 'left';
        ctx.fillText('Fallback Mode', 10, 20);
        
        ctx.fillStyle = '#888';
        ctx.font = '11px Arial';
        ctx.fillText(`FPS: ~60`, 10, 35);
        ctx.fillText(`Blink: ${state.isBlinking ? '👁' : '👀'}`, 70, 35);
    }
    
    /**
     * Set eye tracking for fallback mode
     */
    lookAt(x, y) {
        if (this.isFallback && this.fallbackState) {
            this.fallbackState.mouseX = x;
            this.fallbackState.mouseY = y;
        }
    }
    
    /**
     * Set expression for fallback mode
     */
    setExpression(expr) {
        if (this.isFallback && this.fallbackState) {
            this.fallbackState.expression = expr;
        }
    }
    
    // FIX: WebGL context lost/restored handlers
    _onContextLost() {
        console.warn('[Live2DManager] WebGL context lost, model may need reloading');
        this.modelLoaded = false;
        
        // Notify the app about context loss
        if (this.onContextLost) {
            this.onContextLost();
        }
        
        // Try to restore context automatically after a short delay
        setTimeout(() => {
            console.log('[Live2DManager] Attempting to restore WebGL context...');
            this._restoreWebGLContext();
        }, 1000);
    }
    
    _onContextRestored() {
        console.log('[Live2DManager] WebGL context restored event fired');
        // Reinitialize WebGL resources
        this._restoreWebGLContext();
    }
    
    _restoreWebGLContext() {
        // Try to restore the WebGL context and reload the model
        if (!this.gl || this.gl.isContextLost()) {
            console.log('[Live2DManager] Context still lost, waiting...');
            setTimeout(() => this._restoreWebGLContext(), 500);
            return;
        }
        
        console.log('[Live2DManager] Restoring WebGL context and reloading model...');
        
        // Reload the model if one was loaded
        if (this.modelPath && this.modelLoaded) {
            this.loadModel(this.modelPath).then(() => {
                console.log('[Live2DManager] Model reloaded after context restoration');
            }).catch((error) => {
                console.error('[Live2DManager] Failed to reload model:', error);
            });
        }
    }
    
    async initialize() {
        console.log('[Live2DManager] initialize called');
        
        return new Promise(async (resolve) => {
            let isResolved = false;
            const isLowEndDevice = navigator.hardwareConcurrency <= 2 || navigator.deviceMemory <= 2;
            const timeout = isLowEndDevice ? 20000 : 15000;
            
            console.log('[Live2DManager] initialize timeout:', timeout);
            console.log('[Live2DManager] this.sdk:', !!this.sdk, 'this.cubismSdk:', !!this.cubismSdk, 'this.isFallback:', this.isFallback);
            
            const timeoutId = setTimeout(() => {
                if (!isResolved) {
                    isResolved = true;
                    console.error(`[Live2DManager] Initialization timed out after ${timeout}ms`);
                    resolve(false);
                }
            }, timeout);

            try {
                // 如果是 fallback manager 或已經有 sdk，直接返回成功
                if (this.isFallback || (this.sdk && Object.keys(this.sdk).length >= 0)) {
                    console.log('[Live2DManager] Using fallback/skipping full initialization');
                    isResolved = true;
                    clearTimeout(timeoutId);
                    resolve(true);
                    return;
                }
                
                if (!this.sdk) {
                    console.log('[Live2DManager] Calling _tryLoadSDK');
                    await this._tryLoadSDK();
                }
                
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    const success = !!(this.sdk && (this.cubismSdk || this.isFallback));
                    console.log('[Live2DManager] Initialization result:', success);
                    resolve(success);
                }
            } catch (error) {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    console.error('[Live2DManager] Initialization failed:', error);
                    resolve(false);
                }
            }
        });
    }
    
    async loadModel(modelPath) {
        console.log('[Live2DManager] Loading Live2D model from:', modelPath);
        console.log('[Live2DManager] SDK 5 mode - using official Framework classes');

        // Check if we're in fallback mode
        if (this.isFallback) {
            console.log('[Live2DManager] Fallback mode active - using 2D animated character');
            return true;
        }

        // SDK 5 requires Core SDK + Framework
        if (!window.Live2DCubismCore) {
            console.error('[Live2DManager] Core SDK not loaded');
            return false;
        }
        if (!window.Live2DCubismFramework) {
            console.error('[Live2DManager] Framework SDK not loaded');
            return false;
        }

        const C = window.Live2DCubismFramework;
        const isLowEndDevice = navigator.hardwareConcurrency <= 2 || navigator.deviceMemory <= 2;
        const timeout = isLowEndDevice ? 30000 : 20000;

        return new Promise(async (resolve) => {
            let isResolved = false;

            const timeoutId = setTimeout(() => {
                if (!isResolved) {
                    isResolved = true;
                    console.error('[Live2DManager] Model loading timed out: ' + modelPath);
                    resolve(false);
                }
            }, timeout);

            try {
                // Paths
                const modelJsonPath = modelPath.endsWith('/') ? modelPath + 'miara_pro_t03.model3.json' : modelPath + '/miara_pro_t03.model3.json';
                const mocPath = modelPath.endsWith('/') ? modelPath + 'miara_pro_t03.moc3' : modelPath + '/miara_pro_t03.moc3';

                console.log('[Live2DManager] Loading MOC3 from:', mocPath);

                // Load MOC3 file as ArrayBuffer
                const mocResponse = await fetch(mocPath);
                if (!mocResponse.ok) {
                    throw new Error('Failed to load MOC3: ' + mocResponse.status);
                }
                const mocArrayBuffer = await mocResponse.arrayBuffer();
                console.log('[Live2DManager] MOC3 loaded, size:', mocArrayBuffer.byteLength);

                // Create model from MOC using official Framework API
                const cubismModel = C.CubismModel.fromMoc(new Uint8Array(mocArrayBuffer));
                if (!cubismModel) {
                    throw new Error('Failed to create CubismModel from MOC');
                }
                console.log('[Live2DManager] CubismModel created successfully');

                // Load model3.json
                let textureUrls = [];
                let physicsPath = null;
                let posePath = null;
                let expressionPaths = [];

                // Get directory of model3.json for relative paths
                const modelJsonDir = modelJsonPath.substring(0, modelJsonPath.lastIndexOf('/'));

                try {
                    const response = await fetch(modelJsonPath);
                    if (response.ok) {
                        const modelJson = await response.json();
                        console.log('[Live2DManager] Model JSON loaded');

                        if (modelJson.FileReferences && modelJson.FileReferences.Textures) {
                            textureUrls = modelJson.FileReferences.Textures.map(function(t) { 
                                // Texture paths are relative to model3.json location
                                return modelJsonDir + '/' + t;
                            });
                            console.log('[Live2DManager] Texture URLs:', textureUrls);
                        }
                        if (modelJson.FileReferences && modelJson.FileReferences.Physics) {
                            physicsPath = modelJsonDir + '/' + modelJson.FileReferences.Physics;
                        }
                        if (modelJson.FileReferences && modelJson.FileReferences.Pose) {
                            posePath = modelJsonDir + '/' + modelJson.FileReferences.Pose;
                        }
                        if (modelJson.FileReferences && modelJson.FileReferences.Expressions) {
                            expressionPaths = modelJson.FileReferences.Expressions.map(function(e) {
                                return modelJsonDir + '/' + e.File;
                            });
                        }
                    }
                } catch (e) {
                    console.warn('[Live2DManager] Could not load model3.json:', e);
                }

                // Fallback textures
                if (textureUrls.length === 0) {
                    textureUrls = [modelPath + '/miara_pro_t03.4096/texture_00.png'];
                }

                // Create WebGL renderer using official Framework
                const renderer = new C.CubismRenderer_WebGL(this.gl);
                renderer.startFrame();
                renderer.setMoc(cubismModel);
                renderer.initialize();

                // Load textures
                console.log('[Live2DManager] Loading textures:', textureUrls);
                for (let i = 0; i < textureUrls.length; i++) {
                    const texResponse = await fetch(textureUrls[i]);
                    if (!texResponse.ok) {
                        console.warn('[Live2DManager] Failed to load texture:', textureUrls[i]);
                        continue;
                    }
                    const blob = await texResponse.blob();
                    const bitmap = await createImageBitmap(blob);
                    renderer.bindTexture(i, bitmap);
                }

                // Store references
                this.sdkModel = cubismModel;
                this.sdkRenderer = renderer;
                this.currentModelPath = modelPath;
                this.currentModel = 'miara_pro_t03';
                this.modelLoaded = true;

                console.log('[Live2DManager] SDK 5 model loaded successfully');

                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                }
                resolve(true);

            } catch (error) {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    console.error('[Live2DManager] Failed to load model:', error);
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
        // Use FrontendUtils throttled animation for consistent FPS control
        const throttledAnimation = FrontendUtils.createThrottledAnimation(this.targetFPS, () => {
            this.render();
            this.updateFPS(performance.now());
        });

        this.animationFrameId = throttledAnimation.frameId;
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
        // SDK 5 mode - use our WebGL renderer
        if (this.sdkModel && this.sdkRenderer) {
            this.sdkRenderer.render();
            this.updateAnimations();
            return;
        }
        
        // Legacy wrapper mode
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
    
    /**
     * 根据身体部位触发相应的动作和表情
     * @param {string} bodyPart - 身体部位 (head, face, chest, leftHand, rightHand)
     */
    triggerMotionByPart(bodyPart) {
        if (!this.modelLoaded) {
            return;
        }
        
        console.log(`[Live2DManager] Triggering motion for body part: ${bodyPart}`);
        
        // 根据身体部位映射到表情
        const partExpressionMap = {
            'head': 'surprised',
            'face': 'happy',
            'chest': 'shy',
            'leftHand': 'happy',
            'rightHand': 'happy'
        };
        
        // 根据身体部位映射到动作组
        const partMotionMap = {
            'head': 'tap_body',
            'face': 'tap_face',
            'chest': 'tap_body',
            'leftHand': 'tap_body',
            'rightHand': 'tap_body'
        };
        
        // 设置表情
        const expression = partExpressionMap[bodyPart] || 'happy';
        this.setExpression(expression);
        
        // 播放动作
        const motionGroup = partMotionMap[bodyPart] || 'tap_body';
        this.playMotion(motionGroup, '01');
        
        // 参数微调
        switch(bodyPart) {
            case 'head':
                this.setParameter('ParamAngleX', 0);
                this.setParameter('ParamAngleY', 0);
                break;
            case 'face':
                this.setParameter('ParamBodyAngleX', 10);
                break;
            case 'chest':
                this.setParameter('ParamBodyAngleX', -5);
                this.setParameter('ParamBreath', 1.0);
                break;
            case 'leftHand':
            case 'rightHand':
                this.setParameter('ParamArmLA', bodyPart === 'leftHand' ? 10 : 0);
                this.setParameter('ParamArmRA', bodyPart === 'rightHand' ? 10 : 0);
                break;
        }
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
    
    setAnimationParameters() {
        if (this.wrapper && this.live2dModel) {
            // Update live2dModel.parameters directly if wrapper.setParameter is not available
            if (typeof this.wrapper.setParameter === 'function') {
                // Use wrapper.setParameters to update multiple parameters
                this.wrapper.setParameters(this.parameters);
            } else if (this.live2dModel.parameters) {
                // Fallback: update live2dModel.parameters directly
                for (const [name, value] of Object.entries(this.parameters)) {
                    if (this.live2dModel.parameters[name] !== undefined) {
                        this.live2dModel.parameters[name] = value;
                    }
                }
            }
        }
    }
    
    setParameter(name, value) {
        if (!this.modelLoaded) {
            return;
        }
        
        this.parameters[name] = value;
        
        if (this.sdk && this.wrapper) {
            if (typeof this.wrapper.setParameter === 'function') {
                this.wrapper.setParameter(name, value);
            } else if (this.live2dModel && this.live2dModel.parameters) {
                // Fallback: update live2dModel.parameters directly
                if (this.live2dModel.parameters[name] !== undefined) {
                    this.live2dModel.parameters[name] = value;
                }
            }
        }
    }
    
    setResolutionScale(scale) {
        this.resolutionScale = Math.max(0.5, Math.min(2.0, scale));
        
        if (this.wrapper && this.wrapper.isLoaded) {
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
            if (typeof this.wrapper.setPhysicsEnabled === 'function') {
                this.wrapper.setPhysicsEnabled(this.advancedAnimations && this.physicsEnabled);
            }
        }
    }
    
    setPhysicsEnabled(enabled) {
        this.physicsEnabled = enabled;
        this.updateAdvancedAnimations();
    }
    
    setTargetFPS(fps) {
        this.targetFPS = Math.max(30, Math.min(120, fps));
        
        if (this.wrapper && typeof this.wrapper.setTargetFPS === 'function') {
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
    
    lookAt(x, y) {
        // Update eye tracking parameters
        if (this.wrapper && typeof this.wrapper.setParameter === 'function') {
            // Clamp values to valid range
            const clampedX = Math.max(-1, Math.min(1, x));
            const clampedY = Math.max(-1, Math.min(1, y));
            
            // Update eye ball position
            this.wrapper.setParameter('ParamEyeBallX', clampedX * 30);
            this.wrapper.setParameter('ParamEyeBallY', clampedY * 30);
            
            // Update body angle slightly for more natural movement
            this.wrapper.setParameter('ParamBodyAngleX', clampedX * 10);
            this.wrapper.setParameter('ParamBodyAngleY', clampedY * 10);
            
            // Update head angle
            this.wrapper.setParameter('ParamAngleX', clampedX * 20);
            this.wrapper.setParameter('ParamAngleY', clampedY * 20);
        }
    }
    
    shutdown() {
        console.log('Shutting down Live2D Manager...');
        
        this.stopAnimation();
        
        // Clean up fallback animation
        if (this.fallbackAnimationId) {
            cancelAnimationFrame(this.fallbackAnimationId);
            this.fallbackAnimationId = null;
        }
        
        // Clean up SDK 5 resources
        if (this.sdkRenderer) {
            this.sdkRenderer.destroy();
            this.sdkRenderer = null;
        }
        if (this.sdkModel) {
            this.sdkModel.release();
            this.sdkModel = null;
        }
        
        if (this.wrapper) {
            this.wrapper.destroy();
        }
        
        this.sdk = null;
        this.modelLoaded = false;
        this.isRunning = false;
        this.isFallback = false;
        this.currentModel = null;
        
        console.log('Live2D Manager shutdown complete');
    }
}

// ============================================================================

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DManager;
}
