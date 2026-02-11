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
        // SRI 哈希值用于验证 CDN 资源完整性
        const cdnSources = [
            {
                src: 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
                integrity: null // Live2D 官方 CDN 未提供 SRI 哈希
            },
            {
                src: 'https://cdn.jsdelivr.net/npm/@live2d/cubism-core@4.0.0/live2dcubismcore.min.js',
                integrity: null // jsDelivr 未为特定版本提供固定 SRI
            },
            {
                src: 'https://unpkg.com/@live2d/cubism-core@4.0.0/live2dcubismcore.min.js',
                integrity: null // unpkg 未提供 SRI
            },
            {
                src: '../libs/live2dcubismcore.min.js',
                integrity: null // 本地文件不需要 SRI
            }
        ];

        let lastError = null;

        // 优先尝试本地备份（最安全）
        const localSource = cdnSources[3];
        try {
            console.log(`優先嘗試從本地加載 Live2D Cubism Core: ${localSource.src}`);
            await this._loadScript(localSource.src, localSource.integrity);
            console.log(`成功從本地加載 Live2D Cubism Core`);
            return;
        } catch (error) {
            console.warn(`本地加載失敗:`, error.message);
            lastError = error;
        }

        // 本地失败后尝试 CDN
        for (const source of cdnSources.slice(0, 3)) {
            try {
                console.log(`嘗試從 CDN 加載 Live2D Cubism Core: ${source.src}`);
                await this._loadScript(source.src, source.integrity);
                console.log(`成功從 CDN 加載 Live2D Cubism Core`);
                return;
            } catch (error) {
                console.warn(`從 ${source.src} 加載失敗:`, error.message);
                lastError = error;
                continue;
            }
        }

        // 所有源都失敗，嘗試加載fallback
        try {
            console.log('所有CDN源失敗，嘗試加載本地fallback...');
            await this._loadScript('../libs/live2d-fallback.js', null);
            await window.loadLocalLive2DSDK();
            console.log('成功加載本地fallback SDK');
            return;
        } catch (fallbackError) {
            console.error('Fallback也失敗:', fallbackError);
        }

        // 所有嘗試都失敗
        throw lastError || new Error('Failed to load Live2D Cubism Core from all sources');
    }
    
    async _loadScript(src, integrity = null) {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.crossOrigin = 'anonymous';
        script.timeout = 8000; // 8秒超時

        // 添加 SRI (Subresource Integrity) 验证
        if (integrity) {
            script.integrity = integrity;
        }

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
        const modelPath = settings.modelPath;
        console.log('[loadModel] Loading from:', modelPath);
        
        try {
            // Step 1: Load model3.json first to get file references
            console.log('[loadModel] Step 1: Loading model3.json...');
            const model3Response = await this.loadFileAsArrayBuffer(`local://${modelPath}`);
            const textDecoder = new TextDecoder();
            this.model3Json = JSON.parse(textDecoder.decode(model3Response));
            console.log('[loadModel] model3.json loaded:', JSON.stringify(this.model3Json.FileReferences, null, 2));
            
            // Get base directory from model path
            const lastSlash = modelPath.lastIndexOf('/');
            const baseDir = modelPath.substring(0, lastSlash + 1);
            console.log('[loadModel] baseDir:', baseDir);
            
            // Step 2: Load MOC3 file using FileReferences
            const mocFileName = this.model3Json.FileReferences?.Moc || 'miara_pro_t03.moc3';
            const mocPath = `local://${baseDir}${mocFileName}`;
            console.log('[loadModel] Step 2: Loading MOC3 from:', mocPath);
            const mocBuffer = await this.loadFileAsArrayBuffer(mocPath);
            this.moc3 = new Uint8Array(mocBuffer);
            console.log('[loadModel] MOC3 loaded, size:', mocBuffer.byteLength);
            
            // Step 3: Load CDI3 file (optional)
            const cdiFileName = this.model3Json.FileReferences?.DisplayInfo;
            if (cdiFileName) {
                const cdiPath = `local://${baseDir}${cdiFileName}`;
                console.log('[loadModel] Step 3: Loading CDI3 from:', cdiPath);
                const cdiBuffer = await this.loadFileAsArrayBuffer(cdiPath);
                this.cdi3Json = JSON.parse(textDecoder.decode(cdiBuffer));
            } else {
                console.log('[loadModel] Step 3: No CDI3 file');
            }
            
            // Step 4: Load Physics (optional)
            const physicsFileName = this.model3Json.FileReferences?.Physics;
            if (physicsFileName) {
                const physicsPath = `local://${baseDir}${physicsFileName}`;
                console.log('[loadModel] Step 4: Loading Physics from:', physicsPath);
                const physicsBuffer = await this.loadFileAsArrayBuffer(physicsPath);
                this.physics3Json = JSON.parse(textDecoder.decode(physicsBuffer));
            } else {
                console.log('[loadModel] Step 4: No Physics file');
            }
            
            // Step 5: Load Textures
            const textureFileNames = this.model3Json.FileReferences?.Textures || ['texture_00.png'];
            console.log('[loadModel] Step 5: Loading textures:', textureFileNames);
            this.texturePaths = [];
            for (const texFile of textureFileNames) {
                const texPath = `local://${baseDir}${texFile}`;
                console.log('[loadModel] Texture path:', texPath);
                this.texturePaths.push(texPath);
            }
            
            // Step 6: Create the model
            console.log('[loadModel] Step 6: Creating Cubism model...');
            await this.createCubismModel();
            await this.setupMotionGroups();
            await this.setupModelParameters();
            this.createRenderer();
            
            this.isLoaded = true;
            
            if (this.callbacks.onLoaded) {
                this.callbacks.onLoaded();
            }
            
            console.log('[loadModel] SUCCESS: Live2D model loaded successfully');
            return true;
        } catch (error) {
            console.error('[loadModel] FAILED:', error.message);
            console.error('[loadModel] Stack:', error.stack);
            this.isLoaded = false;
            throw error;
        }
    }
    
    async loadMoc3File(modelPath) {
        const moc3Paths = this.findFile(modelPath, '.moc3');
        
        console.log('Possible MOC3 files:', moc3Paths);
        
        // Try each possible path
        for (const moc3Path of moc3Paths) {
            try {
                console.log('Trying to load MOC3 file:', moc3Path);
                
                // Try to load the file
                const arrayBuffer = await this.loadFileAsArrayBuffer(moc3Path);
                
                // Debug: Check the structure of Moc
                if (!this.moc3) {
                    console.log('CubismCore.Moc:', this.cubismSdk.Moc);
                    if (this.cubismSdk.Moc) {
                        console.log('CubismCore.Moc keys:', Object.keys(this.cubismSdk.Moc));
                    }
                }
                
                // Try different ways to access Moc
                let MocClass = this.cubismSdk.Moc || this.cubismSdk.MOC3;
                
                // Check if MocClass has create method
                if (typeof MocClass === 'object') {
                    // Try to find create method in MocClass
                    if (typeof MocClass.create === 'function') {
                        this.moc3 = MocClass.create(arrayBuffer);
                    } else if (MocClass.fromArrayBuffer) {
                        this.moc3 = MocClass.fromArrayBuffer(arrayBuffer);
                    } else if (MocClass.fromArrayBuffer) {
                        this.moc3 = MocClass.fromArrayBuffer(arrayBuffer);
                    } else {
                        // Try to find create method in nested properties
                        for (const key of Object.keys(MocClass)) {
                            if (typeof MocClass[key] === 'function' && (key.includes('create') || key.includes('load') || key.includes('from'))) {
                                console.log('Trying to use MocClass.' + key);
                                this.moc3 = MocClass[key](arrayBuffer);
                                break;
                            }
                        }
                    }
                } else if (typeof MocClass === 'function') {
                    // MocClass is a constructor
                    this.moc3 = new MocClass(arrayBuffer);
                }
                
                if (!this.moc3) {
                    throw new Error('Failed to create MOC3 instance');
                }
                
                // Debug: Check if moc3 has _ptr property
                console.log('MOC3 instance:', this.moc3);
                console.log('MOC3._ptr:', this.moc3._ptr);
                
                if (!this.moc3._ptr) {
                    throw new Error('MOC3 instance does not have _ptr property');
                }
                
                if (this.moc3.releaseBytes) {
                    this.moc3.releaseBytes(arrayBuffer);
                }
                
                console.log('MOC3 file loaded successfully:', moc3Path);
                return;
            } catch (error) {
                console.warn('Failed to load MOC3 file:', moc3Path, error.message);
                continue;
            }
        }
        
        throw new Error('Failed to load MOC3 file from any source');
    }
    
    async loadFileAsArrayBuffer(filePath) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', filePath, true);
            xhr.responseType = 'arraybuffer';
            
            xhr.onload = () => {
                if (xhr.status === 200 || xhr.status === 0) {
                    resolve(xhr.response);
                } else {
                    reject(new Error(`Failed to load file: ${xhr.status} ${xhr.statusText}`));
                }
            };
            
            xhr.onerror = () => {
                reject(new Error(`Failed to load file: ${filePath}`));
            };
            
            xhr.send();
        });
    }
    
            async loadTexture(modelPath) {
                console.log('Looking for texture files in:', modelPath);
                
                // Ensure WebGL context is still valid
                if (!this.gl) {
                    console.warn('WebGL context is null, attempting to recreate...');
                    const glOptions = {
                        alpha: false,
                        antialias: false,
                        preserveDrawingBuffer: true,
                        powerPreference: 'low-power',
                        desynchronized: true,
                        failIfMajorPerformanceCaveat: false
                    };
                    
                    this.gl = this.canvas.getContext('webgl2', glOptions) || 
                              this.canvas.getContext('webgl', glOptions) ||
                              this.canvas.getContext('experimental-webgl', glOptions);
                    
                    if (!this.gl) {
                        throw new Error('Failed to recreate WebGL context');
                    }
                    
                    console.log('WebGL context recreated');
                }
                
                // Build base path for textures
                // Extract directory from modelPath - it points to model3.json file
                let basePath = modelPath;
                
                // Convert to URL-like format for consistent path handling
                let filePath = modelPath;
                if (modelPath.startsWith('local://')) {
                    // Convert local:// URL to file path
                    filePath = modelPath.startsWith('local:///') 
                        ? modelPath.substring(9)  // Remove local:///
                        : modelPath.substring(8);  // Remove local://
                } else if (!modelPath.startsWith('/') && !modelPath.includes(':')) {
                    // Relative path, prepend current directory
                    filePath = '/' + modelPath;
                } else if (!modelPath.startsWith('/')) {
                    // Has drive letter (Windows) or other format
                    filePath = modelPath;
                }
                
                // Use URL to properly handle path separators
                try {
                    const url = new URL('file://' + filePath);
                    filePath = url.pathname;
                } catch (e) {
                    // URL parsing failed, use manual parsing
                    const lastDot = filePath.lastIndexOf('.');
                    if (lastDot > filePath.lastIndexOf('/')) {
                        filePath = filePath.substring(0, lastDot);
                    }
                }
                
                // Get directory by removing the filename
                basePath = filePath.substring(0, filePath.lastIndexOf('/') + 1);
                
                // Ensure basePath ends with /
                if (!basePath.endsWith('/')) {
                    basePath = basePath + '/';
                }
                
                // Get texture paths from model3.json if available
                const texturePaths = [];
                if (this.model3Json?.FileReferences?.Textures) {
                    for (const t of this.model3Json.FileReferences.Textures) {
                        if (!t.startsWith('/') && !t.includes(':')) {
                            texturePaths.push(basePath + t);
                        } else {
                            texturePaths.push(t);
                        }
                    }
                }
                
                // Add fallback paths
                const possiblePaths = [
                    ...texturePaths,
                    basePath + 'texture_00.png',
                    basePath + 'texture.png',
                    basePath + 'texture.jpg',
                    basePath + 'miara_pro_t03.4096/texture_00.png',
                    basePath + 'miara_pro_t03.4096/texture.png',
                    basePath + 'miara_pro_t03.4096/texture.jpg',
                ];
                
                for (const texturePath of possiblePaths) {
                    try {
                        console.log('Trying to load texture:', texturePath);
                        
                        await new Promise((resolve, reject) => {
                            const image = new Image();
                            image.src = texturePath;
                            image.onload = () => {
                                this.createTexture(image);
                                console.log('Texture loaded successfully:', texturePath);
                                resolve();
                            };
                            image.onerror = () => {
                                reject(new Error('Failed to load texture'));
                            };
                        });
                        
                        return;  // Successfully loaded texture
                    } catch (error) {
                        console.warn('Failed to load texture:', texturePath, error.message);
                        continue;
                    }
                }
                
                throw new Error('Failed to load texture from any source');
            }    
    createTexture(image) {
        if (!this.gl) {
            console.error('WebGL context is null, cannot create texture');
            return null;
        }
        
        const texture = this.gl.createTexture();
        if (!texture) {
            console.error('Failed to create texture');
            return null;
        }
        
        // Get max texture size
        const maxTextureSize = this.gl.getParameter(this.gl.MAX_TEXTURE_SIZE);
        console.log('Max texture size:', maxTextureSize);
        
        // Auto-scale texture if too large
        let imageToUse = image;
        let originalWidth = image.width;
        let originalHeight = image.height;
        
        // Limit texture size to 512x512 for better performance on laptops
        const maxAllowedSize = 512;
        
        if (image.width > maxAllowedSize || image.height > maxAllowedSize) {
            const scale = Math.min(maxAllowedSize / image.width, maxAllowedSize / image.height);
            const newWidth = Math.floor(image.width * scale);
            const newHeight = Math.floor(image.height * scale);
            
            console.log(`Scaling texture from ${image.width}x${image.height} to ${newWidth}x${newHeight}`);
            
            // Create canvas for scaling
            const canvas = document.createElement('canvas');
            canvas.width = newWidth;
            canvas.height = newHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(image, 0, 0, newWidth, newHeight);
            
            // Use canvas directly as texture source (more efficient than toDataURL)
            imageToUse = canvas;
        }
        
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
            imageToUse
        );
        
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MIN_FILTER, this.gl.LINEAR);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_MAG_FILTER, this.gl.LINEAR);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_S, this.gl.CLAMP_TO_EDGE);
        this.gl.texParameteri(this.gl.TEXTURE_2D, this.gl.TEXTURE_WRAP_T, this.gl.CLAMP_TO_EDGE);
        
        this.texture = texture;
        
        // Also add to textures array for renderer
        if (!this.textures) {
            this.textures = [];
        }
        this.textures.push(texture);
        
        const finalWidth = imageToUse.width || imageToUse.naturalWidth || originalWidth;
        const finalHeight = imageToUse.height || imageToUse.naturalHeight || originalHeight;
        
        console.log('Texture created:', finalWidth, 'x', finalHeight, 
                    (originalWidth !== finalWidth ? `(scaled from ${originalWidth}x${originalHeight})` : ''),
                    'Total textures:', this.textures.length);
    }
    
    async loadPhysics(modelPath) {
        const physicsPaths = this.findFile(modelPath, '.physics3.json');
        
        console.log('Possible physics files:', physicsPaths);
        
        // Try each possible path
        for (const physicsPath of physicsPaths) {
            try {
                console.log('Trying to load physics file:', physicsPath);
                
                // Use XMLHttpRequest for local files in Electron
                const arrayBuffer = await this.loadFileAsArrayBuffer(physicsPath);
                const textDecoder = new TextDecoder();
                const jsonString = textDecoder.decode(arrayBuffer);
                this.physicsJson = JSON.parse(jsonString);
                
                console.log('Physics file loaded successfully:', physicsPath);
                return;
            } catch (error) {
                console.warn('Failed to load physics file:', physicsPath, error.message);
                continue;
            }
        }
        
        throw new Error('Failed to load physics file from any source');
    }
    
    async loadModel3File(modelPath) {
        const model3Paths = this.findFile(modelPath, '.model3.json');
        
        console.log('Possible model3 files:', model3Paths);
        
        // Try each possible path
        for (const model3Path of model3Paths) {
            try {
                console.log('Trying to load model3 file:', model3Path);
                
                // Use XMLHttpRequest for local files in Electron
                const arrayBuffer = await this.loadFileAsArrayBuffer(model3Path);
                const textDecoder = new TextDecoder();
                const jsonString = textDecoder.decode(arrayBuffer);
                this.model3Json = JSON.parse(jsonString);
                
                console.log('Model3 file loaded successfully:', model3Path);
                return;
            } catch (error) {
                console.warn('Failed to load model3 file:', model3Path, error.message);
                continue;
            }
        }
        
        // Model3.json is optional
        console.warn('Model3.json not found, using defaults');
        this.model3Json = {};
    }
    
    async loadCdi3File(modelPath) {
        const cdi3Paths = this.findFile(modelPath, '.cdi3.json');
        
        console.log('Possible CDI3 files:', cdi3Paths);
        
        // Try each possible path
        for (const cdi3Path of cdi3Paths) {
            try {
                console.log('Trying to load CDI3 file:', cdi3Path);
                
                // Use XMLHttpRequest for local files in Electron
                const arrayBuffer = await this.loadFileAsArrayBuffer(cdi3Path);
                const textDecoder = new TextDecoder();
                const jsonString = textDecoder.decode(arrayBuffer);
                this.cdi3Json = JSON.parse(jsonString);
                
                console.log('CDI3 file loaded successfully:', cdi3Path);
                return;
            } catch (error) {
                console.warn('Failed to load CDI3 file:', cdi3Path, error.message);
                continue;
            }
        }
        
        // CDI3.json is optional
        console.warn('CDI3.json not found, using defaults');
        this.cdi3Json = {};
    }
    
    findFile(basePath, extension) {
        console.log('[findFile] basePath:', basePath, 'extension:', extension);
        
        const normalizedPath = basePath.replace(/\\/g, '/');

        // Remove trailing slash if present
        let cleanPath = normalizedPath.endsWith('/') ? normalizedPath.slice(0, -1) : normalizedPath;

        // Check if basePath is already a complete file path (ends with the extension)
        const pathExt = cleanPath.substring(cleanPath.lastIndexOf('.'));
        const isCompletePath = pathExt === extension;
        console.log('[findFile] pathExt:', pathExt, 'isCompletePath:', isCompletePath);
        
        // Get the directory path (for finding files)
        let dirPath;
        try {
            const url = new URL(basePath);
            const pathname = url.pathname;
            if (isCompletePath) {
                // Remove the filename to get directory
                const lastSlash = pathname.lastIndexOf('/');
                dirPath = pathname.substring(0, lastSlash + 1);
            } else {
                const lastSlash = pathname.lastIndexOf('/');
                dirPath = pathname.endsWith('/') ? pathname : pathname.substring(0, lastSlash + 1);
            }
        } catch (e) {
            if (isCompletePath) {
                const lastSlash = cleanPath.lastIndexOf('/');
                dirPath = cleanPath.substring(0, lastSlash + 1);
            } else {
                const lastSlash = cleanPath.lastIndexOf('/');
                dirPath = cleanPath.substring(0, lastSlash + 1);
            }
        }

        if (!extension.startsWith('.')) {
            extension = '.' + extension;
        }

        // If basePath is already a complete file path, return it as the first option
        if (isCompletePath) {
            const fileName = cleanPath.substring(cleanPath.lastIndexOf('/') + 1);
            const possibleNames = [fileName];
            const result = possibleNames.map(name => `local://${dirPath}${name}`);
            console.log('[findFile] Returning:', result);
            return result;
        }

        // Get the model directory name (not the model file name!)
        // e.g., from "/path/to/model/model3.json" extract "model"
        let modelDirName;
        try {
            const url = new URL(basePath);
            const pathname = url.pathname;
            // Find second-to-last slash to get directory name
            const secondLastSlash = pathname.substring(0, pathname.length - 1).lastIndexOf('/');
            modelDirName = pathname.substring(secondLastSlash + 1, pathname.length - 1);
        } catch (e) {
            const parts = cleanPath.split('/');
            // The last part is the model file name, the second-to-last is the directory name
            modelDirName = parts[parts.length - 2];
        }

        // Return all possible paths based on model directory name
        const possibleNames = [
            `${modelDirName}${extension}`,           // e.g., miara_pro.moc3
            `${modelDirName}_t03${extension}`,      // e.g., miara_pro_t03.moc3
            `${modelDirName}_t00${extension}`,      // e.g., miara_pro_t00.moc3
        ];

        // Return all possible paths with local:// protocol for Electron
        const result = possibleNames.map(name => `local://${dirPath}${name}`);
        console.log('[findFile] Returning:', result);
        return result;
    }
    
    async createCubismModel() {
        console.log('Creating Cubism model...');
        
        console.log('CubismSdk.Model:', this.cubismSdk.Model);
        if (this.cubismSdk.Model) {
            console.log('CubismSdk.Model keys:', Object.keys(this.cubismSdk.Model));
        }
        
        // Check WebGL context
        if (!this.gl) {
            throw new Error('WebGL context is null');
        }
        
        // Try different ways to create model
        try {
            if (typeof this.cubismSdk.Model === 'function') {
                // Model is a constructor
                console.log('Using Model constructor');
                this.live2dModel = new this.cubismSdk.Model(this.moc3);
                
                // Debug: Check model structure
                console.log('Model created, checking structure...');
                if (this.live2dModel.drawables) {
                    console.log('Drawables object type:', typeof this.live2dModel.drawables);
                    console.log('Drawables methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this.live2dModel.drawables)));
                    console.log('Drawables own methods:', Object.getOwnPropertyNames(this.live2dModel.drawables));
                }
                if (this.live2dModel.parameters) {
                    console.log('Parameters object type:', typeof this.live2dModel.parameters);
                    console.log('Parameters methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this.live2dModel.parameters)));
                }
            } else if (typeof this.cubismSdk.Model === 'object') {
                // Model is a namespace
                console.log('Model is a namespace');
                
                // Check if moc is valid
                if (!this.moc3 || !this.moc3._ptr) {
                    throw new Error('MOC3 is invalid or missing _ptr');
                }
                
                // Try fromMoc method
                if (typeof this.cubismSdk.Model.fromMoc === 'function') {
                    console.log('Using Model.fromMoc');
                    this.live2dModel = this.cubismSdk.Model.fromMoc(this.moc3);
                } else if (typeof this.cubismSdk.Model.create === 'function') {
                    console.log('Using Model.create');
                    this.live2dModel = this.cubismSdk.Model.create(this.moc3);
                } else {
                    throw new Error('No valid method found to create model');
                }
            }
            
            if (!this.live2dModel) {
                throw new Error('Failed to create Live2D model instance');
            }
            
            console.log('Live2D model created:', this.live2dModel);
            console.log('Live2D model._ptr:', this.live2dModel._ptr);
            
            // Create renderer if method exists (optional)
            if (typeof this.live2dModel.createRenderer === 'function') {
                this.live2dModel.createRenderer(this.gl);
            } else {
                console.warn('createRenderer method not found, renderer setup skipped');
            }
            
            // Update model if method exists (optional)
            if (typeof this.live2dModel.update === 'function') {
                this.live2dModel.update();
            } else {
                console.warn('update method not found, model update skipped');
            }
            
            // Release MOC3 if method exists (optional)
            if (typeof this.live2dModel.releaseMoc3 === 'function') {
                this.live2dModel.releaseMoc3();
            }
            
            this.moc3 = null;
            
            console.log('Cubism model created successfully');
        } catch (error) {
            console.error('Failed to create Cubism model:', error);
            throw error;
        }
    }
    
    async setupMotionGroups() {
        console.log('Setting up motion groups...');
        
        // Check if live2dModel has createMotionManager method
        if (typeof this.live2dModel.createMotionManager === 'function') {
            this.motionManager = this.live2dModel.createMotionManager();
        } else {
            console.warn('live2dModel.createMotionManager not found, motion setup skipped');
            return;
        }
        
        // Check if model3Json has motion data
        if (!this.model3Json || !this.model3Json.FileReferences || !this.model3Json.FileReferences.Motions) {
            console.warn('No motion data found in model3.json');
            return;
        }
        
        const motionGroups = this.model3Json.FileReferences.Motions;
        
        for (const [groupName, groupData] of Object.entries(motionGroups)) {
            const group = await this.createMotionGroup(groupName, groupData);
            if (this.motionManager && typeof this.motionManager.addMotionGroup === 'function') {
                this.motionManager.addMotionGroup(group);
            }
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
        
        // Check if model3Json has parameter data
        if (!this.model3Json || !this.model3Json.FileReferences || !this.model3Json.FileReferences.Parameters) {
            console.warn('No parameter data found in model3.json');
            return;
        }
        
        const parameters = this.model3Json.FileReferences.Parameters;
        
        for (const [paramName, paramData] of Object.entries(parameters)) {
            // Check if live2dModel has findModelParameterById method
            if (typeof this.live2dModel.findModelParameterById === 'function') {
                const parameter = this.live2dModel.findModelParameterById(paramData.Id);
                if (parameter) {
                    parameter.value = paramData.Value;
                    if (typeof this.live2dModel.addParameter === 'function') {
                        this.live2dModel.addParameter(parameter);
                    }
                }
            }
        }
        
        console.log(`Loaded ${Object.keys(parameters).length} parameters`);
    }
    
    createRenderer() {
        console.log('Creating renderer...');
        
        // Check if live2dModel has createRenderer method
        if (typeof this.live2dModel.createRenderer === 'function') {
            this.renderer = this.live2dModel.createRenderer();
            this.renderer.setWebGLContext(this.gl);
            this.renderer.startAlpha(this.gl);
            this.renderer.update(this.live2dModel);
            if (typeof this.renderer.setRenderLoop === 'function') {
                this.renderer.setRenderLoop(this.gl, () => this.render());
            }
            console.log('Renderer created');
        } else {
            console.warn('live2dModel.createRenderer not found, using fallback renderer');
            // Create a simple fallback renderer using Cubism SDK core methods
            const self = this;
            // Don't initialize self.textures here, let it reference this.textures dynamically
            this.renderer = {
                update: (model) => {
                    // Update is handled by model.update()
                },
                draw: (gl) => {
                    if (!self.live2dModel) {
                        return;
                    }
                    
                    console.log('[Renderer] draw() called');
                    
                    try {
                        // Clear the canvas
                        gl.clearColor(0.0, 0.0, 0.0, 0.0);
                        gl.clear(gl.COLOR_BUFFER_BIT);
                        
                        // Get canvas dimensions
                        const width = self.canvas.width;
                        const height = self.canvas.height;
                        
                        // Setup viewport
                        gl.viewport(0, 0, width, height);
                        
                        // Enable blending for transparency
                        gl.enable(gl.BLEND);
                        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
                        
                        // Try to render using actual Live2D drawables
                        if (self.live2dModel.drawables && self.live2dModel.drawables.count > 0) {
                            const drawables = self.live2dModel.drawables;
                            const drawableCount = drawables.count;
                            
                            console.log(`drawableCount: ${drawableCount}`);
                            console.log(`drawables.getDrawableCount: ${typeof drawables.getDrawableCount}`);
                            
                            console.log(`Rendering ${drawableCount} drawables`);
                            
                            // Create shader program if not exists
                            if (!self.shaderProgram) {
                                const vertexShaderSource = `
                                    attribute vec2 a_position;
                                    attribute vec2 a_texCoord;
                                    varying vec2 v_texCoord;
                                    void main() {
                                        // Convert from 0-1 to -1 to 1 NDC space
                                        vec4 position = vec4(a_position * 2.0 - 1.0, 0.0, 1.0);
                                        // Flip Y axis for proper rendering
                                        position.y = -position.y;
                                        gl_Position = position;
                                        v_texCoord = a_texCoord;
                                    }
                                `;
                                
                                const fragmentShaderSource = `
                                    precision mediump float;
                                    varying vec2 v_texCoord;
                                    uniform sampler2D u_texture;
                                    uniform float u_opacity;
                                    void main() {
                                        vec4 texColor = texture2D(u_texture, v_texCoord);
                                        gl_FragColor = vec4(texColor.rgb, texColor.a * u_opacity);
                                    }
                                `;
                                
                                const vertexShader = gl.createShader(gl.VERTEX_SHADER);
                                gl.shaderSource(vertexShader, vertexShaderSource);
                                gl.compileShader(vertexShader);
                                
                                const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
                                gl.shaderSource(fragmentShader, fragmentShaderSource);
                                gl.compileShader(fragmentShader);
                                
                                self.shaderProgram = gl.createProgram();
                                gl.attachShader(self.shaderProgram, vertexShader);
                                gl.attachShader(self.shaderProgram, fragmentShader);
                                gl.linkProgram(self.shaderProgram);
                            }
                            
                            gl.useProgram(self.shaderProgram);
                            
                            // Render each drawable
                            // Debug: check self and this
                            console.log('Debug - self.textures:', self.textures ? self.textures.length : 'undefined');
                            console.log('Debug - this.textures:', this.textures ? this.textures.length : 'undefined');
                            const textures = self.textures || this.textures || [];
                            console.log(`Starting to render ${drawableCount} drawables`);
                            console.log(`Texture count: ${textures.length}`);
                            console.log(`About to enter drawable loop`);
                            
                            let successfullyRendered = 0;
                            let skippedInvisible = 0;
                            let skippedNoTexture = 0;
                            let skippedNoData = 0;
                            let loopCount = 0;
                            
                            for (let i = 0; i < drawableCount; i++) {
                                loopCount++;
                                try {
                                    // Safe access to opacities
                                    let opacity = 1.0;
                                    if (drawables.opacities && typeof drawables.opacities === 'object' && 'length' in drawables.opacities) {
                                        opacity = drawables.opacities[i] !== undefined ? drawables.opacities[i] : 1.0;
                                    }
                                    
                                    // Skip invisible drawables
                                    if (opacity <= 0.0) {
                                        skippedInvisible++;
                                        continue;
                                    }
                                    
                                    const textureIndex = drawables.textureIndices ? drawables.textureIndices[i] : -1;
                                    
                                    // Check if we have texture for this drawable
                                    if (textureIndex >= 0 && textures[textureIndex]) {
                                        // Safe access to vertexCounts and indexCounts
                                        if (!drawables.vertexCounts || typeof drawables.vertexCounts[i] === 'undefined') {
                                            console.error(`vertexCounts[${i}] is undefined`);
                                            skippedNoData++;
                                            continue;
                                        }
                                        if (!drawables.indexCounts || typeof drawables.indexCounts[i] === 'undefined') {
                                            console.error(`indexCounts[${i}] is undefined`);
                                            skippedNoData++;
                                            continue;
                                        }
                                        
                                        const vertexCount = drawables.vertexCounts[i];
                                        const indexCount = drawables.indexCounts[i];
                                        
                                        if (vertexCount > 0 && indexCount > 0) {
                                            // Get vertex positions and UVs - check each property
                                            if (!drawables.vertexPositions) {
                                                console.error(`vertexPositions is undefined for drawable ${i}`);
                                                skippedNoData++;
                                                continue;
                                            }
                                            if (!drawables.vertexUvs) {
                                                console.error(`vertexUvs is undefined for drawable ${i}`);
                                                skippedNoData++;
                                                continue;
                                            }
                                            if (!drawables.indices) {
                                                console.error(`indices is undefined for drawable ${i}`);
                                                skippedNoData++;
                                                continue;
                                            }
                                            
                                            const vertexPositions = drawables.vertexPositions;
                                            const vertexUvs = drawables.vertexUvs;
                                            const indices = drawables.indices;
                                            
                                            // Debug: check data sizes
                                            if (i < 3) {
                                                console.log(`Drawable ${i}: vertexCount=${vertexCount}, indexCount=${indexCount}`);
                                                console.log(`  Drawable ID: ${drawables.ids ? drawables.ids[i] : 'N/A'}`);
                                                console.log(`  vertexPositions[${i}] type:`, vertexPositions[i] ? vertexPositions[i].constructor.name : 'null', 
                                                          'length:', vertexPositions[i] ? vertexPositions[i].length : 'null');
                                                console.log(`  vertexUvs[${i}] type:`, vertexUvs[i] ? vertexUvs[i].constructor.name : 'null',
                                                          'length:', vertexUvs[i] ? vertexUvs[i].length : 'null');
                                                console.log(`  indices[${i}] type:`, indices[i] ? indices[i].constructor.name : 'null',
                                                          'length:', indices[i] ? indices[i].length : 'null');
                                                if (vertexPositions[i] && vertexPositions[i].length > 0) {
                                                    const arr = vertexPositions[i];
                                                    const values = [];
                                                    for (let k = 0; k < Math.min(6, arr.length); k++) {
                                                        values.push(arr[k]);
                                                    }
                                                    console.log(`  First 3 vertexPositions:`, values);
                                                }
                                            }
                                            
                                            // Get the actual data for this drawable
                                            const drawableVertexPositions = vertexPositions[i];
                                            const drawableVertexUvs = vertexUvs[i];
                                            const drawableIndices = indices[i];
                                            
                                            if (!drawableVertexPositions || !drawableVertexUvs || !drawableIndices) {
                                                console.error(`Missing data for drawable ${i}`);
                                                skippedNoData++;
                                                continue;
                                            }
                                            
                                            // Create vertex buffer
                                            const vertexData = new Float32Array(vertexCount * 4);
                                            for (let j = 0; j < vertexCount; j++) {
                                                const baseIndex = j * 4;
                                                vertexData[baseIndex] = drawableVertexPositions[j * 2];
                                                vertexData[baseIndex + 1] = drawableVertexPositions[j * 2 + 1];
                                                vertexData[baseIndex + 2] = drawableVertexUvs[j * 2];
                                                vertexData[baseIndex + 3] = drawableVertexUvs[j * 2 + 1];
                                            }
                                            
                                            const vertexBuffer = gl.createBuffer();
                                            gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
                                            gl.bufferData(gl.ARRAY_BUFFER, vertexData, gl.STATIC_DRAW);
                                            
                                            // Create index buffer
                                            let indexArray;
                                            if (drawableIndices instanceof Uint16Array || drawableIndices instanceof Uint32Array) {
                                                indexArray = drawableIndices;
                                            } else if (Array.isArray(drawableIndices)) {
                                                indexArray = new Uint16Array(drawableIndices);
                                            } else {
                                                console.error(`Invalid indices type for drawable ${i}:`, drawableIndices.constructor.name);
                                                skippedNoData++;
                                                continue;
                                            }
                                            
                                            // Check if indices reference valid vertices
                                            let maxIndex = 0;
                                            for (let j = 0; j < indexCount && j < indexArray.length; j++) {
                                                if (indexArray[j] > maxIndex) maxIndex = indexArray[j];
                                            }
                                            
                                            if (maxIndex >= vertexCount) {
                                                console.error(`Drawable ${i}: max index ${maxIndex} >= vertexCount ${vertexCount}`);
                                                skippedNoData++;
                                                continue;
                                            }
                                            
                                            const indexBuffer = gl.createBuffer();
                                            gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
                                            gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indexArray, gl.STATIC_DRAW);
                                            
                                            // Set up attributes
                                            const positionLocation = gl.getAttribLocation(self.shaderProgram, 'a_position');
                                            const texCoordLocation = gl.getAttribLocation(self.shaderProgram, 'a_texCoord');
                                            
                                            gl.enableVertexAttribArray(positionLocation);
                                            gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 16, 0);
                                            
                                            gl.enableVertexAttribArray(texCoordLocation);
                                            gl.vertexAttribPointer(texCoordLocation, 2, gl.FLOAT, false, 16, 8);
                                            
                                            // Bind texture
                                            gl.activeTexture(gl.TEXTURE0);
                                            gl.bindTexture(gl.TEXTURE_2D, self.textures[textureIndex]);
                                            gl.uniform1i(gl.getUniformLocation(self.shaderProgram, 'u_texture'), 0);
                                            gl.uniform1f(gl.getUniformLocation(self.shaderProgram, 'u_opacity'), opacity);
                                            
                                            // Draw - use appropriate index type based on max index
                                            const indexType = (maxIndex > 65535) ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT;
                                            gl.drawElements(gl.TRIANGLES, indexCount, indexType, 0);
                                            
                                            successfullyRendered++;
                                            
                                            // Clean up
                                            gl.deleteBuffer(vertexBuffer);
                                            gl.deleteBuffer(indexBuffer);
                                        }
                                    } else {
                                        skippedNoTexture++;
                                    }
                                } catch (drawableError) {
                                    console.error(`Error rendering drawable ${i}:`, drawableError);
                                    // Skip problematic drawable
                                    continue;
                                }
                            }
                            
                            console.log(`Loop completed. Total iterations: ${loopCount}`);
                            console.log(`Rendering stats: ${successfullyRendered} rendered, ${skippedInvisible} invisible, ${skippedNoTexture} no texture, ${skippedNoData} no data`);
                        } else {
                            // Fallback: draw animated placeholder if no drawables
                            if (!self.placeholderShader) {
                                const vertexShaderSource = `
                                    attribute vec2 a_position;
                                    void main() {
                                        gl_Position = vec4(a_position, 0.0, 1.0);
                                    }
                                `;
                                
                                const fragmentShaderSource = `
                                    precision mediump float;
                                    uniform float u_time;
                                    void main() {
                                        float pulse = sin(u_time * 3.0) * 0.1 + 0.9;
                                        gl_FragColor = vec4(0.4, 0.6, 0.9, 0.7 * pulse);
                                    }
                                `;
                                
                                const vertexShader = gl.createShader(gl.VERTEX_SHADER);
                                gl.shaderSource(vertexShader, vertexShaderSource);
                                gl.compileShader(vertexShader);
                                
                                const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
                                gl.shaderSource(fragmentShader, fragmentShaderSource);
                                gl.compileShader(fragmentShader);
                                
                                self.placeholderShader = gl.createProgram();
                                gl.attachShader(self.placeholderShader, vertexShader);
                                gl.attachShader(self.placeholderShader, fragmentShader);
                                gl.linkProgram(self.placeholderShader);
                            }
                            
                            gl.useProgram(self.placeholderShader);
                            
                            const vertices = new Float32Array([
                                -0.3, -0.3,
                                 0.3, -0.3,
                                -0.3,  0.3,
                                 0.3,  0.3
                            ]);
                            
                            const positionBuffer = gl.createBuffer();
                            gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
                            gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
                            
                            const positionLocation = gl.getAttribLocation(self.placeholderShader, 'a_position');
                            gl.enableVertexAttribArray(positionLocation);
                            gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);
                            
                            gl.uniform1f(gl.getUniformLocation(self.placeholderShader, 'u_time'), Date.now() / 1000.0);
                            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
                        }
                        
                        // Update model
                        if (typeof self.live2dModel.update === 'function') {
                            self.live2dModel.update();
                        }
                        
                    } catch (error) {
                        console.error('Renderer draw error:', error);
                        console.error('Error stack:', error.stack);
                    }
                },
                setWebGLContext: (gl) => {
                    self.gl = gl;
                }
            };
            console.log('Fallback renderer created with Cubism SDK drawing');
        }
    }
    
    render() {
        console.log('[Wrapper] render() called, isLoaded:', this.isLoaded, 'isRunning:', this.isRunning);
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
        
        console.log('[Wrapper] start() called');
        this.isRunning = true;
        this.lastUpdate = Date.now();
        console.log('Renderer started');
        
        // Start render loop
        const self = this;
        function renderLoop() {
            if (self.isRunning) {
                self.render();
                requestAnimationFrame(renderLoop);
            }
        }
        requestAnimationFrame(renderLoop);
    }
    
    stop() {
        this.isRunning = false;
        console.log('Renderer stopped');
    }
    
    resize(width, height) {
        console.log(`Resizing to ${width}x${height}`);
        
        // Update canvas dimensions
        this.canvas.width = width;
        this.canvas.height = height;
        
        // Check WebGL context
        if (!this.gl) {
            console.warn('WebGL context is null in resize');
            return;
        }
        
        // Check if live2dModel exists
        if (!this.live2dModel) {
            console.warn('live2dModel is null in resize');
            return;
        }
        
        // Check if cubismSdk.Viewport exists
        if (this.cubismSdk && this.cubismSdk.Viewport) {
            const resizeViewport = this.cubismSdk.Viewport.getViewport(width, height);
            
            this.gl.viewport(
                resizeViewport.x,
                resizeViewport.y,
                resizeViewport.width,
                resizeViewport.height
            );
            
            this.cubismSdk.Viewport.update(width, height, this.gl);
        } else {
            // Fallback: use direct viewport setting
            this.gl.viewport(0, 0, width, height);
        }
        
        // Update renderer if it exists
        if (this.renderer && typeof this.renderer.update === 'function') {
            this.renderer.update(this.live2dModel);
        }
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

// Export to global for browser environment
if (typeof window !== 'undefined') {
    window.Live2DCubismWrapper = Live2DCubismWrapper;
    console.log('Live2DCubismWrapper exported to global');
}