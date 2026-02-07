/**
 * Angela AI - Live2D Cubism Web SDK Wrapper
 * 
 * Wrapper for official Live2D Cubism Web SDK
 * Handles SDK initialization, model loading, and rendering
 */

class Live2DCubismWrapper {
    constructor(canvas) {
        this.canvas = canvas;
        this.gl = null;
        this.sdkLoaded = false;
        this.cubismSdk = null;
        this.live2dModel = null;
        this.cubismModel = null;
        this.motionManager = null;
        this.moc3 = null;
        this.texture = null;
        this.renderer = null;
        this.isLoaded = false;
        this.isRunning = false;
        this.currentMotion = null;
        this.currentMotionFade = 0;
        this.lastUpdate = 0;
        this.targetFPS = 60;
        this.updateInterval = 1000 / 60;
        
        this.callbacks = {
            onLoaded: null,
            onMotionFinished: null,
            onError: null
        };
        
        this.loadSDK();
    }
    
    async loadSDK() {
        console.log('Loading Live2D Cubism Web SDK...');
        
        try {
            if (window.Live2DCubismCore) {
                this.cubismSdk = window.Live2DCubismCore;
                this.sdkLoaded = true;
                console.log('Live2D Cubism Core loaded from window');
                return;
            }
            
            await this.loadCubismScript();
            await this.waitForCubismSDK();
            
            this.sdkLoaded = true;
            console.log('Live2D Cubism Web SDK loaded successfully');
        } catch (error) {
            console.error('Failed to load Live2D Cubism SDK:', error);
            throw error;
        }
    }
    
    async loadCubismScript() {
        // 嘗試多種CDN源，包括本地備份
        const cdnSources = [
            'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
            'https://cdn.jsdelivr.net/npm/@live2d/cubism-core@4.0.0/live2dcubismcore.min.js',
            'https://unpkg.com/@live2d/cubism-core@4.0.0/live2dcubismcore.min.js',
            '../libs/live2dcubismcore.min.js' // 本地備份
        ];
        
        let lastError = null;
        
        for (const src of cdnSources) {
            try {
                console.log(`嘗試從 ${src} 加載 Live2D Cubism Core...`);
                await this._loadScript(src);
                console.log(`成功從 ${src} 加載 Live2D Cubism Core`);
                return;
            } catch (error) {
                console.warn(`從 ${src} 加載失敗:`, error.message);
                lastError = error;
                continue;
            }
        }
        
        // 所有源都失敗，嘗試加載fallback
        try {
            console.log('所有CDN源失敗，嘗試加載本地fallback...');
            await this._loadScript('../libs/live2d-fallback.js');
            await window.loadLocalLive2DSDK();
            console.log('成功加載本地fallback SDK');
            return;
        } catch (fallbackError) {
            console.error('Fallback也失敗:', fallbackError);
        }
        
        // 所有嘗試都失敗
        throw lastError || new Error('Failed to load Live2D Cubism Core from all sources');
    }
    
    async _loadScript(src) {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.crossOrigin = 'anonymous';
        script.timeout = 8000; // 8秒超時
        
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                reject(new Error(`Script load timeout: ${src}`));
            }, script.timeout);
            
            script.onload = () => {
                clearTimeout(timeoutId);
                resolve();
            };
            
            script.onerror = () => {
                clearTimeout(timeoutId);
                reject(new Error(`Script load error: ${src}`));
            };
            
            document.head.appendChild(script);
        });
    }
    
    waitForCubismSDK() {
        return new Promise((resolve, reject) => {
            const checkInterval = setInterval(() => {
                if (window.Live2DCubismCore) {
                    clearInterval(checkInterval);
                    console.log('Live2D Cubism SDK detected and ready');
                    resolve();
                }
            }, 200); // 檢查間隔調整為200ms
            
            // 動態超時：根據網路條件調整
            const timeout = navigator.onLine ? 8000 : 12000;
            setTimeout(() => {
                clearInterval(checkInterval);
                reject(new Error(`Failed to load Live2D Cubism SDK within ${timeout}ms`));
            }, timeout);
        });
    }
    
    async initializeWebGL() {
        console.log('Initializing WebGL context...');
        
        try {
            this.gl = this.canvas.getContext('webgl2', {
                alpha: true,
                antialias: true,
                depth: false,
                stencil: false,
                preserveDrawingBuffer: true,
                premultipliedAlpha: false
            }) || this.canvas.getContext('webgl');
            
            if (!this.gl) {
                throw new Error('WebGL not supported');
            }
            
            const ext = this.gl.getExtension('OES_element_index_uint');
            this.gl.getExtension('OES_standard_derivatives');
            this.gl.getExtension('OES_texture_float_linear');
            this.gl.getExtension('OES_texture_float');
            
            console.log('WebGL context initialized successfully');
        } catch (error) {
            console.error('Failed to initialize WebGL:', error);
            throw error;
        }
    }
    
    async loadModel(settings) {
        console.log('Loading Live2D model:', settings.modelPath);
        
        try {
            await this.loadMoc3File(settings.modelPath);
            await this.loadTexture(settings.modelPath);
            await this.loadPhysics(settings.modelPath);
            await this.loadModel3File(settings.modelPath);
            await this.loadCdi3File(settings.modelPath);
            
            await this.createCubismModel();
            await this.setupMotionGroups();
            await this.setupModelParameters();
            this.createRenderer();
            
            this.isLoaded = true;
            
            if (this.callbacks.onLoaded) {
                this.callbacks.onLoaded();
            }
            
            console.log('Live2D model loaded successfully');
            
            return true;
        } catch (error) {
            console.error('Failed to load Live2D model:', error);
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
            throw error;
        }
    }
    
    async loadMoc3File(modelPath) {
        const moc3Path = this.findFile(modelPath, '.moc3');
        
        console.log('Loading MOC3 file:', moc3Path);
        
        const response = await fetch(moc3Path);
        const arrayBuffer = await response.arrayBuffer();
        
        this.moc3 = this.cubismSdk.MOC3.create(arrayBuffer);
        this.moc3.releaseBytes(arrayBuffer);
        
        console.log('MOC3 file loaded');
    }
    
    async loadTexture(modelPath) {
        const texturePath = this.findFile(modelPath, '.png') || this.findFile(modelPath, '.jpg') || this.findFile(modelPath, '.jpeg');
        
        console.log('Loading texture:', texturePath);
        
        return new Promise((resolve, reject) => {
            const image = new Image();
            image.src = texturePath;
            image.onload = () => {
                this.createTexture(image);
                resolve();
            };
            image.onerror = reject;
        });
    }
    
    createTexture(image) {
        const texture = this.gl.createTexture();
        this.gl.bindTexture(this.gl.TEXTURE_2D, texture);
        
        const level = 0;
        const internalFormat = this.gl.RGBA;
        const srcFormat = this.gl.RGBA;
        const srcType = this.gl.UNSIGNED_BYTE;
        
        this.gl.texImage2D(
            this.gl.TEXTURE_2D,
            level,
            internalFormat,
            srcFormat,
            srcType,
            image
        );
        
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MIN_FILTER, this.gl.LINEAR);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MAG_FILTER, this.gl.LINEAR);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_S, this.gl.CLAMP_TO_EDGE);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_T, this.gl.CLAMP_TO_EDGE);
        
        this.texture = texture;
        console.log('Texture created:', image.width, 'x', image.height);
    }
    
    async loadPhysics(modelPath) {
        const physicsPath = this.findFile(modelPath, '.physics3.json');
        
        console.log('Loading physics file:', physicsPath);
        
        const response = await fetch(physicsPath);
        this.physicsJson = await response.json();
        
        console.log('Physics file loaded:', Object.keys(this.physicsJson));
    }
    
    async loadModel3File(modelPath) {
        const model3Path = this.findFile(modelPath, '.model3.json');
        
        console.log('Loading model3 file:', model3Path);
        
        const response = await fetch(model3Path);
        this.model3Json = await response.json();
        
        console.log('Model3 file loaded:', this.model3Json.FileReferences);
    }
    
    async loadCdi3File(modelPath) {
        const cdi3Path = this.findFile(modelPath, '.cdi3.json');
        
        console.log('Loading CDI3 file:', cdi3Path);
        
        const response = await fetch(cdi3Path);
        this.cdi3Json = await response.json();
        
        console.log('CDI3 file loaded');
    }
    
    findFile(basePath, extension) {
        const normalizedPath = basePath.replace(/\\/g, '/');
        const dirPath = normalizedPath.substring(0, normalizedPath.lastIndexOf('/'));
        const fileName = normalizedPath.substring(normalizedPath.lastIndexOf('/'));
        
        if (!extension.startsWith('.')) {
            extension = '.' + extension;
        }
        
        return `${dirPath}/${fileName}${extension}`;
    }
    
    async createCubismModel() {
        console.log('Creating Cubism model...');
        
        this.cubismModel = this.cubismSdk.Model;
        this.live2dModel = new this.cubismModel();
        
        await this.cubismModel.loadFromMoc3(this.moc3, this.physicsJson);
        
        this.live2dModel.saveParameters();
        this.live2dModel.createRenderer(this.gl);
        this.live2dModel.update();
        this.live2dModel.releaseMoc3();
        this.moc3 = null;
        
        console.log('Cubism model created');
    }
    
    async setupMotionGroups() {
        console.log('Setting up motion groups...');
        
        this.motionManager = this.live2dModel.createMotionManager();
        
        const motionGroups = this.model3Json.FileReferences.Motions;
        
        for (const [groupName, groupData] of Object.entries(motionGroups)) {
            const group = await this.createMotionGroup(groupName, groupData);
            this.motionManager.addMotionGroup(group);
        }
        
        console.log(`Loaded ${Object.keys(motionGroups).length} motion groups`);
    }
    
    async createMotionGroup(groupName, groupData) {
        const group = this.cubismSdk.MotionGroup;
        const groupInstance = new group();
        
        await group.loadfromJsonFile(
            `${groupName}.motion3.json`,
            {
                instance: groupInstance,
                name: groupName,
                path: groupData.File
            }
        );
        
        return groupInstance;
    }
    
    async setupModelParameters() {
        console.log('Setting up model parameters...');
        
        const parameters = this.model3Json.FileReferences.Parameters;
        
        for (const [paramName, paramData] of Object.entries(parameters)) {
            const parameter = this.live2dModel.findModelParameterById(paramData.Id);
            if (parameter) {
                parameter.value = paramData.Value;
                this.live2dModel.addParameter(parameter);
            }
        }
        
        console.log(`Loaded ${Object.keys(parameters).length} parameters`);
    }
    
    createRenderer() {
        console.log('Creating renderer...');
        
        this.renderer = this.live2dModel.createRenderer();
        this.renderer.setWebGLContext(this.gl);
        this.renderer.startAlpha(this.gl);
        this.renderer.update(this.live2dModel);
        this.renderer.setRenderLoop(this.gl, () => this.render());
        
        console.log('Renderer created');
    }
    
    render() {
        if (!this.isLoaded || !this.isRunning) {
            return;
        }
        
        const deltaTime = this.getCurrentDeltaTime();
        this.lastUpdate = Date.now();
        
        this.live2dModel.update(deltaTime);
        this.renderer.update(this.live2dModel);
        this.renderer.draw(this.gl);
        
        this.handleMotionTransitions(deltaTime);
    }
    
    handleMotionTransitions(deltaTime) {
        if (this.currentMotion && this.currentMotionFade < 1.0) {
            this.currentMotionFade += deltaTime * 2;
            
            if (this.currentMotionFade >= 1.0) {
                this.currentMotionFade = 1.0;
                if (this.callbacks.onMotionFinished) {
                    this.callbacks.onMotionFinished(this.currentMotion.name);
                }
            }
        }
    }
    
    getCurrentDeltaTime() {
        const now = Date.now();
        const deltaTime = Math.min(now - this.lastUpdate, 100) / 1000;
        return deltaTime;
    }
    
    async playMotion(groupName, motionName) {
        console.log(`Playing motion: ${groupName}/${motionName}`);
        
        if (!this.isLoaded) {
            return false;
        }
        
        try {
            this.currentMotionFade = 0.0;
            
            const groups = this.motionManager.getMotionGroupAll();
            
            for (const group of groups) {
                if (group.name === groupName) {
                    const motions = group.getMotionCount();
                    
                    for (let i = 0; i < motions; i++) {
                        const motion = group.getMotion(i);
                        if (motion && motion.name === motionName) {
                            this.live2dModel.startMotion(group, motion);
                            this.currentMotion = { group, motion, name: `${groupName}/${motionName}` };
                            
                            if (motion.isLoopFadeIn) {
                                this.currentMotionFade = 0.0;
                            }
                            
                            return true;
                        }
                    }
                }
            }
            
            return false;
        } catch (error) {
            console.error('Failed to play motion:', error);
            return false;
        }
    }
    
    stopMotion() {
        if (this.currentMotion) {
            this.live2dModel.stopAllMotions();
            this.currentMotion = null;
            this.currentMotionFade = 0.0;
            console.log('All motions stopped');
        }
    }
    
    updateParameter(parameterName, value) {
        if (!this.isLoaded) {
            return false;
        }
        
        try {
            const parameter = this.live2dModel.findModelParameterById(parameterName);
            if (parameter) {
                parameter.value = value;
                this.live2dModel.addParameter(parameter);
                this.live2dModel.update();
                return true;
            }
            return false;
        } catch (error) {
            console.error(`Failed to update parameter ${parameterName}:`, error);
            return false;
        }
    }
    
    setExpression(expressionName) {
        if (!this.isLoaded) {
            return false;
        }
        
        console.log(`Setting expression: ${expressionName}`);
        
        const expressionMotions = {
            'neutral': ['neutral_idle'],
            'happy': ['happy_idle', 'happy'],
            'sad': ['sad_idle', 'sad'],
            'angry': ['angry_idle', 'angry'],
            'surprised': ['surprised_idle', 'surprised'],
            'shy': ['shy_idle', 'shy'],
            'love': ['love_idle', 'love']
        };
        
        const motions = expressionMotions[expressionName];
        if (!motions) {
            console.warn(`Unknown expression: ${expressionName}`);
            return false;
        }
        
        const [groupName, motionName] = motions[0].split('/');
        return this.playMotion(groupName, motionName);
    }
    
    resetPose() {
        if (!this.isLoaded) {
            return;
        }
        
        console.log('Resetting pose');
        
        const defaultParameters = {
            'ParamAngleX': 0,
            'ParamAngleY': 0,
            'ParamAngleZ': 0,
            'ParamBodyAngleX': 0,
            'ParamBodyAngleY': 0,
            'ParamBodyAngleZ': 0,
            'ParamEyeBallX': 0,
            'ParamEyeBallY': 0,
            'ParamBreath': 0
        };
        
        for (const [paramName, value] of Object.entries(defaultParameters)) {
            this.updateParameter(paramName, value);
        }
        
        this.setExpression('neutral');
    }
    
    start() {
        if (!this.isLoaded) {
            console.warn('Model not loaded, cannot start');
            return;
        }
        
        this.isRunning = true;
        this.lastUpdate = Date.now();
        console.log('Renderer started');
    }
    
    stop() {
        this.isRunning = false;
        console.log('Renderer stopped');
    }
    
    resize(width, height) {
        if (!this.gl) {
            return;
        }
        
        const resizeViewport = this.cubismSdk.Viewport.getViewport(width, height);
        
        this.gl.viewport(
            resizeViewport.x,
            resizeViewport.y,
            resizeViewport.width,
            resizeViewport.height
        );
        
        this.cubismSdk.Viewport.update(width, height, this.gl);
        
        this.renderer.update(this.live2dModel);
        
        console.log(`Resized to ${width}x${height}`);
    }
    
    onLoaded(callback) {
        this.callbacks.onLoaded = callback;
    }
    
    onMotionFinished(callback) {
        this.callbacks.onMotionFinished = callback;
    }
    
    onError(callback) {
        this.callbacks.onError = callback;
    }
    
    getParameters() {
        if (!this.isLoaded) {
            return {};
        }
        
        const parameters = {};
        const paramCount = this.live2dModel.getModelParameters().getSize();
        
        for (let i = 0; i < paramCount; i++) {
            const param = this.live2dModel.getModelParameters().getAt(i);
            parameters[param.id] = param.value;
        }
        
        return parameters;
    }
    
    getAvailableMotions() {
        if (!this.motionManager) {
            return {};
        }
        
        const motions = {};
        const groups = this.motionManager.getMotionGroupAll();
        
        for (const group of groups) {
            const groupMotions = [];
            const motionCount = group.getMotionCount();
            
            for (let i = 0; i < motionCount; i++) {
                const motion = group.getMotion(i);
                if (motion) {
                    groupMotions.push({
                        name: motion.name,
                        loop: motion.isLoop,
                        fadeIn: motion.isLoopFadeIn
                    });
                }
            }
            
            if (groupMotions.length > 0) {
                motions[group.name] = groupMotions;
            }
        }
        
        return motions;
    }
    
    destroy() {
        this.stop();
        
        if (this.live2dModel) {
            this.live2dModel.deleteRenderer(this.gl);
            this.cubismModel = null;
            this.live2dModel.releaseMoc3();
        }
        
        if (this.gl) {
            this.gl = null;
        }
        
        this.moc3 = null;
        this.cubismSdk = null;
        this.sdkLoaded = false;
        this.isLoaded = false;
        this.isRunning = false;
    }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Live2DCubismWrapper;
}