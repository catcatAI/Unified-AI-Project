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
        // Try multiple CDN sources including local backup
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
            const model3Response = await this.loadFileAsArrayBuffer(modelPath);
            const textDecoder = new TextDecoder();
            this.model3Json = JSON.parse(textDecoder.decode(model3Response));
            console.log('[loadModel] model3.json loaded:', JSON.stringify(this.model3Json.FileReferences, null, 2));

            // Get base directory from model path
            const lastSlash = modelPath.lastIndexOf('/');
            const baseDir = modelPath.substring(0, lastSlash + 1);
            console.log('[loadModel] baseDir:', baseDir);

            // Step 2: Load MOC3 file
            console.log('[loadModel] Step 2: Loading MOC3...');
            const mocFileName = this.model3Json.FileReferences?.Moc || 'miara_pro_t03.moc3';
            const mocPath = `${baseDir}${mocFileName}`;
            await this.loadMoc3File(mocPath);

            // Step 3: Load CDI3 file (optional)
            const cdiFileName = this.model3Json.FileReferences?.DisplayInfo;
            if (cdiFileName) {
                const cdiPath = `${baseDir}${cdiFileName}`;
                console.log('[loadModel] Step 3: Loading CDI3 from:', cdiPath);
                const cdiBuffer = await this.loadFileAsArrayBuffer(cdiPath);
                this.cdi3Json = JSON.parse(textDecoder.decode(cdiBuffer));
            } else {
                console.log('[loadModel] Step 3: No CDI3 file');
            }

            // Step 4: Load Physics (optional)
            const physicsFileName = this.model3Json.FileReferences?.Physics;
            if (physicsFileName) {
                const physicsPath = `${baseDir}${physicsFileName}`;
                console.log('[loadModel] Step 4: Loading Physics from:', physicsPath);
                const physicsBuffer = await this.loadFileAsArrayBuffer(physicsPath);
                this.physics3Json = JSON.parse(textDecoder.decode(physicsBuffer));
            } else {
                console.log('[loadModel] Step 4: No Physics file');
            }

            // Step 5: Initialize WebGL context BEFORE textures (textures need GL)
            console.log('[loadModel] Step 5: Initializing WebGL context...');
            await this.initializeWebGL();

            // Step 6: Load Textures (requires WebGL context)
            const textureFileNames = this.model3Json.FileReferences?.Textures || ['texture_00.png'];
            console.log('[loadModel] Step 6: Loading textures:', textureFileNames);
            this.textures = [];
            for (let texFile of textureFileNames) {
                if (texFile.startsWith('./')) texFile = texFile.substring(2);
                if (texFile.startsWith('/')) texFile = texFile.substring(1);

                const texPath = `${baseDir}${texFile}`;
                console.log('[loadModel] Loading texture path:', texPath);
                const texture = await this.loadTexture(texPath);
                if (texture) {
                    this.textures.push(texture);
                }
            }

            // Step 7: Create the model instance
            console.log('[loadModel] Step 7: Creating Cubism model...');
            await this.createCubismModel();
            await this.setupMotionGroups();
            await this.setupModelParameters();
            this.createRenderer();

            this.isLoaded = true;

            if (this.callbacks.onLoaded) {
                this.callbacks.onLoaded();
            }

            console.log('[loadModel] SUCCESS: Live2D model loaded with ' + this.textures.length + ' textures');
            return true;
        } catch (error) {
            console.error('[loadModel] FAILED:', error.message);
            console.error('[loadModel] Stack:', error.stack);
            this.isLoaded = false;
            throw error;
        }
    }

    async loadMoc3File(modelPath) {
        // Official CubismCore API: Moc.fromArrayBuffer(buffer)
        // Reference: https://docs.live2d.com/cubism-sdk-manual/cubism-core-api-reference/

        const moc3Paths = this.findFile(modelPath, '.moc3');
        console.log('[loadMoc3] Candidate paths:', moc3Paths);

        for (const moc3Path of moc3Paths) {
            try {
                console.log('[loadMoc3] Loading:', moc3Path);
                const arrayBuffer = await this.loadFileAsArrayBuffer(moc3Path);
                console.log('[loadMoc3] ArrayBuffer size:', arrayBuffer.byteLength, 'bytes');

                if (!this.cubismSdk || !this.cubismSdk.Moc) {
                    throw new Error('Live2DCubismCore.Moc is not available');
                }

                // Official API: Live2DCubismCore.Moc.fromArrayBuffer(buffer)
                if (typeof this.cubismSdk.Moc.fromArrayBuffer === 'function') {
                    this.moc3 = this.cubismSdk.Moc.fromArrayBuffer(arrayBuffer);
                } else if (typeof this.cubismSdk.Moc.create === 'function') {
                    // Fallback for older SDK versions
                    this.moc3 = this.cubismSdk.Moc.create(arrayBuffer);
                } else {
                    throw new Error('No valid Moc creation method found (expected fromArrayBuffer or create)');
                }

                if (!this.moc3) {
                    throw new Error('Moc creation returned null — possible corrupted .moc3 file');
                }

                console.log('[loadMoc3] MOC3 loaded successfully:', moc3Path);
                console.log('[loadMoc3] MOC3._ptr:', this.moc3._ptr);
                return;
            } catch (error) {
                console.warn('[loadMoc3] Failed:', moc3Path, error.message);
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
        }

        // Just get directory by removing the filename
        const lastSlash = filePath.lastIndexOf('/');
        if (lastSlash >= 0) {
            basePath = filePath.substring(0, lastSlash + 1);
        } else {
            // If there's no slash, the basepath is just the current dir
            basePath = '';
        }

        // Ensure basePath ends with / if it's not empty
        if (basePath.length > 0 && !basePath.endsWith('/')) {
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

        // Limit texture size for performance (2048 preserves good quality for 4K atlases)
        const maxAllowedSize = 2048;

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
            const result = possibleNames.map(name => `${dirPath}${name}`);
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
        const result = possibleNames.map(name => `${dirPath}${name}`);
        console.log('[findFile] Returning:', result);
        return result;
    }

    async createCubismModel() {
        // Official CubismCore API: Model.fromMoc(moc)
        // Reference: https://docs.live2d.com/cubism-sdk-manual/cubism-core-api-reference/

        console.log('[createModel] Creating Cubism model...');

        if (!this.gl) {
            throw new Error('WebGL context is null — call initializeWebGL() first');
        }

        if (!this.moc3) {
            throw new Error('MOC3 not loaded — call loadMoc3File() first');
        }

        try {
            // Official API: Live2DCubismCore.Model.fromMoc(moc)
            if (this.cubismSdk.Model && typeof this.cubismSdk.Model.fromMoc === 'function') {
                console.log('[createModel] Using Model.fromMoc (official API)');
                this.live2dModel = this.cubismSdk.Model.fromMoc(this.moc3);
            } else if (this.cubismSdk.Model && typeof this.cubismSdk.Model.create === 'function') {
                console.log('[createModel] Using Model.create (fallback)');
                this.live2dModel = this.cubismSdk.Model.create(this.moc3);
            } else if (typeof this.cubismSdk.Model === 'function') {
                console.log('[createModel] Using Model constructor (legacy)');
                this.live2dModel = new this.cubismSdk.Model(this.moc3);
            } else {
                throw new Error('No valid Model creation method found');
            }

            if (!this.live2dModel) {
                throw new Error('Model creation returned null');
            }

            // Initial update to compute drawables
            this.live2dModel.update();

            // Log model info using property access (official API)
            const drawables = this.live2dModel.drawables;
            const parameters = this.live2dModel.parameters;
            const parts = this.live2dModel.parts;
            console.log(`[createModel] Model created successfully:`);
            console.log(`[createModel]   Drawables: ${drawables ? drawables.count : 'N/A'}`);
            console.log(`[createModel]   Parameters: ${parameters ? parameters.count : 'N/A'}`);
            console.log(`[createModel]   Parts: ${parts ? parts.count : 'N/A'}`);

            console.log('[createModel] Cubism model ready');
        } catch (error) {
            console.error('[createModel] FAILED:', error.message);
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
            // Fallback renderer: maps CubismCore model-space coords to WebGL clip-space
            // CubismCore vertex positions are in model canvas units (varies per model)
            // We need to scale them to WebGL clip space [-1, 1] using canvasinfo
            const self = this;

            // Get model canvas info for coordinate transformation
            const canvasinfo = this.live2dModel.canvasinfo;
            let ppUnit = 1.0;
            let originX = 0.0;
            let originY = 0.0;
            let canvasW = 1.0;
            let canvasH = 1.0;
            if (canvasinfo) {
                ppUnit = canvasinfo.PixelsPerUnit || 1.0;
                originX = canvasinfo.OriginX || 0.0;
                originY = canvasinfo.OriginY || 0.0;
                canvasW = canvasinfo.CanvasWidth || 1.0;
                canvasH = canvasinfo.CanvasHeight || 1.0;
                console.log(`[Renderer] Canvas info: ${canvasW}x${canvasH}, PPU=${ppUnit}, Origin=(${originX},${originY})`);
            } else {
                console.warn('[Renderer] No canvasinfo, will auto-detect scale from vertex bounds');
            }

            this.renderer = {
                update: function (model) {
                    // Update is handled by model.update()
                },
                draw: function (gl) {
                    if (!gl) return;
                    if (!self.live2dModel) return;

                    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
                    gl.clear(gl.COLOR_BUFFER_BIT);

                    try {
                        gl.enable(gl.BLEND);
                        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

                        const drawables = self.live2dModel.drawables;
                        if (!drawables) {
                            this.drawPlaceholder(gl);
                            return;
                        }

                        const drawableCount = drawables.count || 0;
                        if (drawableCount <= 0) {
                            this.drawPlaceholder(gl);
                            return;
                        }

                        // Create shader with model-to-clip-space transform
                        if (!self.shaderProgram) {
                            const vs = `
                                attribute vec2 a_position;
                                attribute vec2 a_texCoord;
                                uniform vec4 u_transform; // x: scaleX, y: scaleY, z: offsetX, w: offsetY
                                varying vec2 v_texCoord;
                                void main() {
                                    // Transform model-space coords to clip-space [-1, 1]
                                    vec2 pos = a_position * u_transform.xy + u_transform.zw;
                                    gl_Position = vec4(pos.x, -pos.y, 0.0, 1.0);
                                    v_texCoord = a_texCoord;
                                }
                            `;
                            const fs = `
                                precision mediump float;
                                varying vec2 v_texCoord;
                                uniform sampler2D u_texture;
                                uniform float u_opacity;
                                void main() {
                                    vec4 texColor = texture2D(u_texture, v_texCoord);
                                    gl_FragColor = vec4(texColor.rgb, texColor.a * u_opacity);
                                }
                            `;
                            self.shaderProgram = self.compileShader(vs, fs);
                        }

                        gl.useProgram(self.shaderProgram);

                        // CubismCore with PPU=2000 outputs vertices in [-0.5, 0.5]
                        // We scale 2x to fill [-1, 1] clip space, Y is flipped in shader
                        if (!self._transformComputed) {
                            // Simple 2:1 scale — CubismCore normalizes coords for us
                            // Adjust for canvas aspect ratio
                            const canvasAspect = gl.canvas.width / gl.canvas.height;

                            // Scale uniformly, fit taller dimension
                            self._scaleX = 2.0 / canvasAspect;  // narrower for wide canvases
                            self._scaleY = 2.0;
                            self._offsetX = 0.0;
                            self._offsetY = 0.0;
                            self._transformComputed = true;

                            console.log(`[Renderer] Transform: scale=(${self._scaleX.toFixed(4)}, ${self._scaleY.toFixed(4)}), canvasAspect=${canvasAspect.toFixed(2)}`);
                        }

                        // Upload transform uniform
                        const transformLoc = gl.getUniformLocation(self.shaderProgram, 'u_transform');
                        gl.uniform4f(transformLoc, self._scaleX, self._scaleY, self._offsetX, self._offsetY);

                        let successfullyRendered = 0;
                        const textures = self.textures || [];

                        // Property access (official CubismCore API)
                        const opacities = drawables.opacities;
                        const textureIndices = drawables.textureIndices;
                        const vertexCounts = drawables.vertexCounts;
                        const indexCounts = drawables.indexCounts;
                        const renderOrders = drawables.renderOrders;

                        // Build sorted draw order
                        const sortedIndices = [];
                        for (let i = 0; i < drawableCount; i++) {
                            sortedIndices.push(i);
                        }
                        if (renderOrders) {
                            sortedIndices.sort((a, b) => (renderOrders[a] || 0) - (renderOrders[b] || 0));
                        }

                        // Setup WebGL state for Live2D
                        gl.enable(gl.BLEND);
                        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
                        gl.disable(gl.CULL_FACE);
                        gl.disable(gl.DEPTH_TEST);

                        for (const i of sortedIndices) {
                            const opacity = opacities ? opacities[i] : 1.0;
                            if (opacity <= 0.0) continue;

                            const textureIndex = textureIndices ? textureIndices[i] : 0;
                            const vertexCount = vertexCounts ? vertexCounts[i] : 0;
                            const indexCount = indexCounts ? indexCounts[i] : 0;

                            if (vertexCount > 0 && indexCount > 0 && textures[textureIndex]) {
                                // Official API: array property access
                                const vertexPositions = drawables.vertexPositions ? drawables.vertexPositions[i] : null;
                                const vertexUvs = drawables.vertexUvs ? drawables.vertexUvs[i] : null;
                                const indices = drawables.indices ? drawables.indices[i] : null;

                                if (!vertexPositions || !vertexUvs || !indices) continue;

                                // Ensure we have typed arrays (SDK usually returns them, fallback if not)
                                const posArray = (vertexPositions instanceof Float32Array) ? vertexPositions : new Float32Array(vertexPositions);
                                const uvArray = (vertexUvs instanceof Float32Array) ? vertexUvs : new Float32Array(vertexUvs);
                                const indexArray = (indices instanceof Uint16Array || indices instanceof Uint32Array) ? indices : new Uint16Array(indices);

                                if (!self.vertexBufferPos) self.vertexBufferPos = gl.createBuffer();
                                if (!self.vertexBufferUv) self.vertexBufferUv = gl.createBuffer();
                                if (!self.indexBuffer) self.indexBuffer = gl.createBuffer();

                                // Position Buffer
                                gl.bindBuffer(gl.ARRAY_BUFFER, self.vertexBufferPos);
                                gl.bufferData(gl.ARRAY_BUFFER, posArray, gl.DYNAMIC_DRAW);
                                const posLoc = gl.getAttribLocation(self.shaderProgram, 'a_position');
                                gl.enableVertexAttribArray(posLoc);
                                gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

                                // UV Buffer
                                gl.bindBuffer(gl.ARRAY_BUFFER, self.vertexBufferUv);
                                gl.bufferData(gl.ARRAY_BUFFER, uvArray, gl.DYNAMIC_DRAW);
                                const uvLoc = gl.getAttribLocation(self.shaderProgram, 'a_texCoord');
                                gl.enableVertexAttribArray(uvLoc);
                                gl.vertexAttribPointer(uvLoc, 2, gl.FLOAT, false, 0, 0);

                                // Index Buffer
                                gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.indexBuffer);
                                gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indexArray, gl.DYNAMIC_DRAW);

                                // Texture Setup
                                gl.activeTexture(gl.TEXTURE0);
                                gl.bindTexture(gl.TEXTURE_2D, textures[textureIndex]);
                                gl.uniform1i(gl.getUniformLocation(self.shaderProgram, 'u_texture'), 0);
                                gl.uniform1f(gl.getUniformLocation(self.shaderProgram, 'u_opacity'), opacity);

                                // Draw
                                const indexType = (indexArray instanceof Uint32Array) ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT;
                                gl.drawElements(gl.TRIANGLES, indexCount, indexType, 0);
                                successfullyRendered++;
                            }
                        }

                        if (successfullyRendered === 0) {
                            this.drawPlaceholder(gl);
                        }
                    } catch (e) {
                        console.error('Renderer draw error:', e);
                        this.drawPlaceholder(gl);
                    }
                },
                drawPlaceholder: function (gl) {
                    if (!self.placeholderShader) {
                        const vs = 'attribute vec2 a_position; void main() { gl_Position = vec4(a_position, 0.0, 1.0); }';
                        const fs = 'precision mediump float; uniform vec4 u_color; void main() { gl_FragColor = u_color; }';
                        self.placeholderShader = self.compileShader(vs, fs);
                    }
                    gl.useProgram(self.placeholderShader);
                    const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 500);
                    gl.uniform4f(gl.getUniformLocation(self.placeholderShader, 'u_color'), 0.4, 0.6, 0.9, 0.7 * pulse);

                    if (!self.placeholderBuffer) {
                        self.placeholderBuffer = gl.createBuffer();
                    }
                    const rect = new Float32Array([-0.5, -0.5, 0.5, -0.5, -0.5, 0.5, 0.5, 0.5]);
                    gl.bindBuffer(gl.ARRAY_BUFFER, self.placeholderBuffer);
                    gl.bufferData(gl.ARRAY_BUFFER, rect, gl.STATIC_DRAW);

                    const loc = gl.getAttribLocation(self.placeholderShader, 'a_position');
                    gl.enableVertexAttribArray(loc);
                    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
                    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
                },
                setWebGLContext: function (gl) { self.gl = gl; }
            };
        }
    }

    compileShader(vertexSource, fragmentSource) {
        const gl = this.gl;
        const vShader = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vShader, vertexSource);
        gl.compileShader(vShader);
        if (!gl.getShaderParameter(vShader, gl.COMPILE_STATUS)) {
            console.error('VS Error:', gl.getShaderInfoLog(vShader));
        }
        const fShader = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fShader, fragmentSource);
        gl.compileShader(fShader);
        if (!gl.getShaderParameter(fShader, gl.COMPILE_STATUS)) {
            console.error('FS Error:', gl.getShaderInfoLog(fShader));
        }
        const program = gl.createProgram();
        gl.attachShader(program, vShader);
        gl.attachShader(program, fShader);
        gl.linkProgram(program);
        return program;
    }


    render() {
        if (!this.isLoaded || !this.isRunning) {
            return;
        }

        try {
            const deltaTime = this.getCurrentDeltaTime();
            this.lastUpdate = Date.now();

            // Safe update call - Core Model might not have update()
            if (this.live2dModel && typeof this.live2dModel.update === 'function') {
                this.live2dModel.update(deltaTime);
            } else if (this.cubismModel && typeof this.cubismModel.update === 'function') {
                this.cubismModel.update(deltaTime);
            }

            if (this.renderer) {
                if (typeof this.renderer.update === 'function') {
                    this.renderer.update(this.live2dModel || this.cubismModel);
                }
                if (typeof this.renderer.draw === 'function') {
                    this.renderer.draw(this.gl);
                }
            }

            this.handleMotionTransitions(deltaTime);
        } catch (error) {
            console.error('[Wrapper] Render error:', error);
            // Don't throw, let the loop continue or show fallback
            if (this.renderer && typeof this.renderer.drawPlaceholder === 'function') {
                this.renderer.drawPlaceholder(this.gl);
            }
        }
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

        // Update WebGL viewport if gl exists
        if (this.gl) {
            this.gl.viewport(0, 0, width, height);
        }

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