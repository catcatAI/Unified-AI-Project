/**
 * Angela AI - Settings Page
 * 
 * Handles user preferences and configuration
 */

// Initialize - wait for DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Settings] DOM loaded, initializing...');
    
    // DOM Elements - get after DOM is ready
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.section');
    const notificationContainer = document.getElementById('notification-container');
    
    initializeSettings();
    loadCurrentSettings();
    setupEventListeners();
    
    function showNotification(message, type = 'info') {
        if (!notificationContainer) return;
        
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.style.background = type === 'success' ? '#2ecc71' : 
                                      type === 'error' ? '#e74c3c' : '#3498db';
        notification.textContent = message;
        
        notificationContainer.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    function initializeSettings() {
        console.log('[Settings] Initializing Settings...');
        
        // Load available models
        loadAvailableModels();
        
        // Load available TTS voices
        loadTTSVoices();
    }

    function loadAvailableModels() {
        console.log('[Settings] Loading available models...');
        if (window.electronAPI && window.electronAPI.live2d) {
            window.electronAPI.live2d.getModels().then(models => {
                console.log('[Settings] Found models:', models.map(m => m.name));
                const modelSelect = document.getElementById('model-select');
                if (!modelSelect) {
                    console.error('[Settings] model-select element not found!');
                    return;
                }
                modelSelect.innerHTML = '';
                
                models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name;
                    modelSelect.appendChild(option);
                });
                console.log('[Settings] Models loaded into dropdown');
            }).catch(err => {
                console.error('[Settings] Error loading models:', err);
            });
        } else {
            console.warn('[Settings] electronAPI.live2d not available');
        }
    }

    function loadTTSVoices() {
        const synth = window.speechSynthesis;
        const voices = synth.getVoices();
        
        const voiceSelect = document.getElementById('tts-voice');
        if (!voiceSelect) return;
        
        voiceSelect.innerHTML = '';
        
        if (voices.length === 0) {
            const option = document.createElement('option');
            option.value = 'default';
            option.textContent = 'Default Voice';
            voiceSelect.appendChild(option);
            return;
        }
        
        voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            voiceSelect.appendChild(option);
        });
        
        // Load voices when they become available
        synth.onvoiceschanged = loadTTSVoices;
    }

    function loadCurrentSettings() {
        // Load settings from local storage or Electron config
        const settings = JSON.parse(localStorage.getItem('angela_settings') || '{}');
        console.log('[Settings] Loaded settings:', settings);
        
        // Apply settings to UI
        applySettingsToUI(settings);
    }

    function applySettingsToUI(settings) {
        // General
        const alwaysOnTop = document.getElementById('always-on-top');
        if (alwaysOnTop) alwaysOnTop.checked = settings.alwaysOnTop || false;
        
        const autoStart = document.getElementById('auto-start');
        if (autoStart) autoStart.checked = settings.autoStart || false;
        
        const windowOpacity = document.getElementById('window-opacity');
        if (windowOpacity) {
            windowOpacity.value = settings.windowOpacity || 1;
            const opacityValue = document.getElementById('opacity-value');
            if (opacityValue) opacityValue.textContent = `${Math.round((settings.windowOpacity || 1) * 100)}%`;
        }
        
        const idleMode = document.getElementById('idle-mode');
        if (idleMode) idleMode.checked = settings.idleMode !== false;
        
        const sensitivity = document.getElementById('sensitivity');
        if (sensitivity) sensitivity.value = settings.sensitivity || 'medium';
        
        // Appearance
        const modelSelect = document.getElementById('model-select');
        if (modelSelect) modelSelect.value = settings.model || 'miara_pro';
        
        const modelScale = document.getElementById('model-scale');
        if (modelScale) {
            modelScale.value = settings.modelScale || 1;
            const scaleValue = document.getElementById('scale-value');
            if (scaleValue) scaleValue.textContent = `${(settings.modelScale || 1).toFixed(1)}x`;
        }
        
        const renderMode = document.getElementById('render-mode');
        if (renderMode) renderMode.value = settings.renderMode || 'live2d';
        
        const autoSwitchFallback = document.getElementById('auto-switch-fallback');
        if (autoSwitchFallback) autoSwitchFallback.checked = settings.autoSwitchFallback || false;
        
        const wallpaperMode = document.getElementById('wallpaper-mode');
        if (wallpaperMode) wallpaperMode.value = settings.wallpaperMode || 'overlay';
        
        const wallpaperEffect = document.getElementById('wallpaper-effect');
        if (wallpaperEffect) wallpaperEffect.value = settings.wallpaperEffect || 'none';
        
        // Audio
        const ttsEngine = document.getElementById('tts-engine');
        if (ttsEngine) ttsEngine.value = settings.ttsEngine || 'browser';
        
        const speechRate = document.getElementById('speech-rate');
        if (speechRate) {
            speechRate.value = settings.speechRate || 1;
            const rateValue = document.getElementById('rate-value');
            if (rateValue) rateValue.textContent = `${(settings.speechRate || 1).toFixed(1)}x`;
        }
        
        const speechPitch = document.getElementById('speech-pitch');
        if (speechPitch) {
            speechPitch.value = settings.speechPitch || 1;
            const pitchValue = document.getElementById('pitch-value');
            if (pitchValue) pitchValue.textContent = `${(settings.speechPitch || 1).toFixed(1)}x`;
        }
        
        const speechLanguage = document.getElementById('speech-language');
        if (speechLanguage) speechLanguage.value = settings.speechLanguage || 'en-US';
        
        const continuousRecognition = document.getElementById('continuous-recognition');
        if (continuousRecognition) continuousRecognition.checked = settings.continuousRecognition !== false;
        
        const captureSystemAudio = document.getElementById('capture-system-audio');
        if (captureSystemAudio) captureSystemAudio.checked = settings.captureSystemAudio || false;
        
        // Haptics
        const enableHaptics = document.getElementById('enable-haptics');
        if (enableHaptics) enableHaptics.checked = settings.enableHaptics !== false;
        
        const clickIntensity = document.getElementById('click-intensity');
        if (clickIntensity) {
            clickIntensity.value = settings.clickIntensity || 0.5;
            const clickValue = document.getElementById('click-value');
            if (clickValue) clickValue.textContent = `${Math.round((settings.clickIntensity || 0.5) * 100)}%`;
        }
        
        const touchIntensity = document.getElementById('touch-intensity');
        if (touchIntensity) {
            touchIntensity.value = settings.touchIntensity || 0.8;
            const touchValue = document.getElementById('touch-value');
            if (touchValue) touchValue.textContent = `${Math.round((settings.touchIntensity || 0.8) * 100)}%`;
        }
        
        const emotionIntensity = document.getElementById('emotion-intensity');
        if (emotionIntensity) {
            emotionIntensity.value = settings.emotionIntensity || 0.7;
            const emotionValue = document.getElementById('emotion-value');
            if (emotionValue) emotionValue.textContent = `${Math.round((settings.emotionIntensity || 0.7) * 100)}%`;
        }
        
        // Advanced
        const frameRate = document.getElementById('frame-rate');
        if (frameRate) frameRate.value = settings.frameRate || 60;
        
        const renderQuality = document.getElementById('render-quality');
        if (renderQuality) renderQuality.value = settings.renderQuality || 'medium';
        
        // Network & Cluster
        const backendIp = document.getElementById('backend-ip');
        if (backendIp) backendIp.value = settings.backendIp || '127.0.0.1';
        
        const backendPort = document.getElementById('backend-port');
        if (backendPort) backendPort.value = settings.backendPort || 8000;
        
        const enableCluster = document.getElementById('enable-cluster');
        if (enableCluster) enableCluster.checked = settings.enableCluster || false;
        
        const clusterRole = document.getElementById('cluster-role');
        if (clusterRole) clusterRole.value = settings.clusterRole || 'auto';
        
        const clusterIntegerOnly = document.getElementById('cluster-integer-only');
        if (clusterIntegerOnly) clusterIntegerOnly.checked = settings.clusterIntegerOnly !== false;
        
        const clusterMemoization = document.getElementById('cluster-memoization');
        if (clusterMemoization) clusterMemoization.checked = settings.clusterMemoization !== false;
        
        const nodeName = document.getElementById('node-name');
        if (nodeName) nodeName.value = settings.nodeName || '';
        
        const debugMode = document.getElementById('debug-mode');
        if (debugMode) debugMode.checked = settings.debugMode || false;
        
        const showClickRegions = document.getElementById('show-click-regions');
        if (showClickRegions) showClickRegions.checked = settings.showClickRegions || false;
    }

    function setupEventListeners() {
        console.log('[Settings] Setting up event listeners...');
        
        // Navigation
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const sectionId = item.dataset.section;
                switchSection(sectionId);
            });
        });
        
        // Sliders - update value displays
        setupSlider('window-opacity', 'opacity-value', value => `${Math.round(value * 100)}%`);
        setupSlider('model-scale', 'scale-value', value => `${value.toFixed(1)}x`);
        setupSlider('speech-rate', 'rate-value', value => `${value.toFixed(1)}x`);
        setupSlider('speech-pitch', 'pitch-value', value => `${value.toFixed(1)}x`);
        setupSlider('click-intensity', 'click-value', value => `${Math.round(value * 100)}%`);
        setupSlider('touch-intensity', 'touch-value', value => `${Math.round(value * 100)}%`);
        setupSlider('emotion-intensity', 'emotion-value', value => `${Math.round(value * 100)}%`);
        
        // Buttons
        const loadWallpaperBtn = document.getElementById('load-wallpaper');
        if (loadWallpaperBtn) loadWallpaperBtn.addEventListener('click', loadWallpaper);
        
        const scanDevicesBtn = document.getElementById('scan-devices');
        if (scanDevicesBtn) scanDevicesBtn.addEventListener('click', scanHapticDevices);
        
        const openDevtoolsBtn = document.getElementById('open-devtools');
        if (openDevtoolsBtn) openDevtoolsBtn.addEventListener('click', openDevTools);
        
        const resetSettingsBtn = document.getElementById('reset-settings');
        if (resetSettingsBtn) resetSettingsBtn.addEventListener('click', resetSettings);
        
        const clearCacheBtn = document.getElementById('clear-cache');
        if (clearCacheBtn) clearCacheBtn.addEventListener('click', clearCache);
        
        // Save/Cancel
        const saveBtn = document.getElementById('save');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveSettings);
            console.log('[Settings] Save button event listener attached');
        } else {
            console.error('[Settings] Save button not found!');
        }
        
        const cancelBtn = document.getElementById('cancel');
        if (cancelBtn) cancelBtn.addEventListener('click', cancelSettings);
        
        console.log('[Settings] Event listeners setup complete');
    }

    function setupSlider(sliderId, displayId, formatter) {
        const slider = document.getElementById(sliderId);
        const display = document.getElementById(displayId);
        
        if (slider && display) {
            slider.addEventListener('input', () => {
                display.textContent = formatter(parseFloat(slider.value));
            });
        }
    }

    let monitorInterval = null;

    function switchSection(sectionId) {
        // Update nav items
        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.section === sectionId);
        });
        
        // Update sections
        sections.forEach(section => {
            section.classList.toggle('active', section.id === sectionId);
        });

        // Start/Stop monitoring for network section
        if (sectionId === 'network') {
            startMonitoring();
        } else {
            stopMonitoring();
        }
    }

    function startMonitoring() {
        if (monitorInterval) return;
        
        console.log('[Settings] Starting cluster monitoring...');
        updateMonitorUI(); // Initial update
        monitorInterval = setInterval(updateMonitorUI, 3000);
    }

    function stopMonitoring() {
        if (monitorInterval) {
            console.log('[Settings] Stopping cluster monitoring...');
            clearInterval(monitorInterval);
            monitorInterval = null;
        }
    }

    async function updateMonitorUI() {
        const backendIp = document.getElementById('backend-ip');
        const backendPort = document.getElementById('backend-port');
        if (!backendIp || !backendPort) return;
        
        const ip = backendIp.value || '127.0.0.1';
        const port = backendPort.value || 8000;
        const url = `http://${ip}:${port}/api/v1/system/cluster/status`;

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Backend unreachable');
            const data = await response.json();

            // Update Hardware UI
            const monCpuUsage = document.getElementById('mon-cpu-usage');
            if (monCpuUsage) monCpuUsage.textContent = `${data.hardware.cpu.usage.toFixed(1)}%`;
            
            const monCpuBrand = document.getElementById('mon-cpu-brand');
            if (monCpuBrand) monCpuBrand.textContent = data.hardware.cpu.brand;
            
            const monMemUsage = document.getElementById('mon-mem-usage');
            if (monMemUsage) monMemUsage.textContent = `${data.hardware.memory.usage_percent.toFixed(1)}%`;
            
            const monMemTotal = document.getElementById('mon-mem-total');
            if (monMemTotal) monMemTotal.textContent = `${(data.hardware.memory.total / (1024**3)).toFixed(1)} GB`;
            
            const monPerfTier = document.getElementById('mon-perf-tier');
            if (monPerfTier) monPerfTier.textContent = data.hardware.performance_tier;
            
            const monAiScore = document.getElementById('mon-ai-score');
            if (monAiScore) monAiScore.textContent = data.hardware.ai_capability_score;

            // Update Cluster UI
            const activeNodes = data.cluster.active_nodes;
            const totalNodes = data.cluster.total_nodes;
            const activeNodesEl = document.getElementById('mon-active-nodes');
            if (activeNodesEl) {
                activeNodesEl.textContent = `${activeNodes} / ${totalNodes}`;
                activeNodesEl.className = `status-badge ${activeNodes > 0 ? 'connected' : 'disconnected'}`;
            }

            const nodeList = document.getElementById('node-list');
            if (nodeList) {
                nodeList.innerHTML = '';
                data.cluster.nodes.forEach(node => {
                    const nodeDiv = document.createElement('div');
                    nodeDiv.style.display = 'flex';
                    nodeDiv.style.justifyContent = 'space-between';
                    nodeDiv.style.padding = '4px 0';
                    nodeDiv.style.borderBottom = '1px solid #eee';
                    
                    const statusColor = node.status === 'online' ? '#2ecc71' : '#e74c3c';
                    nodeDiv.innerHTML = `
                        <span><span style="color: ${statusColor}">●</span> ${node.id} (${node.type})</span>
                        <span>Load: ${Math.round(node.load * 100)}%</span>
                    `;
                    nodeList.appendChild(nodeDiv);
                });
            }

            // Update general backend status
            const backendStatus = document.getElementById('backend-status');
            if (backendStatus) {
                backendStatus.textContent = 'Connected';
                backendStatus.className = 'status-badge connected';
            }

        } catch (error) {
            console.warn('[Settings] Monitor update failed:', error);
            const backendStatus = document.getElementById('backend-status');
            if (backendStatus) {
                backendStatus.textContent = 'Disconnected';
                backendStatus.className = 'status-badge disconnected';
            }
        }
    }

    function loadWallpaper() {
        console.log('[Settings] Load wallpaper clicked');
        if (window.electronAPI && window.electronAPI.file) {
            window.electronAPI.file.openDialog({
                filters: [
                    { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'gif', 'webp'] }
                ]
            }).then(result => {
                if (result && !result.canceled && result.filePaths.length > 0) {
                    const imagePath = result.filePaths[0];
                    
                    if (window.electronAPI && window.electronAPI.wallpaper) {
                        window.electronAPI.wallpaper.set(imagePath);
                        showNotification('Wallpaper loaded successfully!', 'success');
                    }
                }
            });
        }
    }

    function scanHapticDevices() {
        console.log('[Settings] Scan haptic devices clicked');
        if (window.angelaApp && window.angelaApp.hapticHandler) {
            window.angelaApp.hapticHandler.discoverDevices().then(devices => {
                console.log('[Settings] Found haptic devices:', devices);
                showNotification(`Found ${devices.length} haptic device(s)`, 'success');
            });
        }
    }

    function openDevTools() {
        console.log('[Settings] Open DevTools clicked');
        if (window.electronAPI && window.electronAPI.window) {
            showNotification('DevTools opened in main window', 'success');
        }
    }

    function resetSettings() {
        console.log('[Settings] Reset settings clicked');
        if (confirm('Are you sure you want to reset all settings to default?')) {
            localStorage.removeItem('angela_settings');
            loadCurrentSettings();
            showNotification('Settings reset to default', 'success');
        }
    }

    function clearCache() {
        console.log('[Settings] Clear cache clicked');
        if (confirm('Are you sure you want to clear all cached data?')) {
            if (window.angelaApp && window.angelaApp.wallpaperHandler) {
                window.angelaApp.wallpaperHandler.cleanup();
            }
            
            showNotification('Cache cleared successfully', 'success');
        }
    }

    function saveSettings() {
        console.log('[Settings] Save button clicked');
        
        try {
            const settings = collectSettings();
            console.log('[Settings] Collected settings:', JSON.stringify(settings, null, 2));
            
            // Save to local storage
            localStorage.setItem('angela_settings', JSON.stringify(settings));
            console.log('[Settings] Settings saved to localStorage');
            
            // Apply settings to application
            applySettingsToApplication(settings);
            
            showNotification('Settings saved successfully!', 'success');
            
            // Close settings window after a delay
            setTimeout(() => {
                console.log('[Settings] Closing settings window...');
                if (window.electronAPI && window.electronAPI.settings) {
                    window.electronAPI.settings.close();
                }
            }, 1000);
        } catch (error) {
            console.error('[Settings] Error saving settings:', error);
            showNotification('Error saving settings: ' + error.message, 'error');
        }
    }

    function cancelSettings() {
        console.log('[Settings] Cancel button clicked');
        if (window.electronAPI && window.electronAPI.settings) {
            window.electronAPI.settings.close();
        }
    }

    function collectSettings() {
        return {
            // General
            alwaysOnTop: document.getElementById('always-on-top')?.checked || false,
            autoStart: document.getElementById('auto-start')?.checked || false,
            windowOpacity: parseFloat(document.getElementById('window-opacity')?.value || 1),
            idleMode: document.getElementById('idle-mode')?.checked !== false,
            sensitivity: document.getElementById('sensitivity')?.value || 'medium',
            
            // Appearance
            model: document.getElementById('model-select')?.value || 'miara_pro',
            modelScale: parseFloat(document.getElementById('model-scale')?.value || 1),
            renderMode: document.getElementById('render-mode')?.value || 'live2d',
            autoSwitchFallback: document.getElementById('auto-switch-fallback')?.checked || false,
            wallpaperMode: document.getElementById('wallpaper-mode')?.value || 'overlay',
            wallpaperEffect: document.getElementById('wallpaper-effect')?.value || 'none',
            
            // Audio
            ttsEngine: document.getElementById('tts-engine')?.value || 'browser',
            voice: document.getElementById('tts-voice')?.value || 'default',
            speechRate: parseFloat(document.getElementById('speech-rate')?.value || 1),
            speechPitch: parseFloat(document.getElementById('speech-pitch')?.value || 1),
            speechLanguage: document.getElementById('speech-language')?.value || 'en-US',
            continuousRecognition: document.getElementById('continuous-recognition')?.checked !== false,
            captureSystemAudio: document.getElementById('capture-system-audio')?.checked || false,
            
            // Haptics
            enableHaptics: document.getElementById('enable-haptics')?.checked !== false,
            clickIntensity: parseFloat(document.getElementById('click-intensity')?.value || 0.5),
            touchIntensity: parseFloat(document.getElementById('touch-intensity')?.value || 0.8),
            emotionIntensity: parseFloat(document.getElementById('emotion-intensity')?.value || 0.7),
            
            // Advanced
            frameRate: parseInt(document.getElementById('frame-rate')?.value || 60),
            renderQuality: document.getElementById('render-quality')?.value || 'medium',
            backendIp: document.getElementById('backend-ip')?.value || '127.0.0.1',
            backendPort: parseInt(document.getElementById('backend-port')?.value || 8000),
            enableCluster: document.getElementById('enable-cluster')?.checked || false,
            clusterRole: document.getElementById('cluster-role')?.value || 'auto',
            clusterIntegerOnly: document.getElementById('cluster-integer-only')?.checked !== false,
            clusterMemoization: document.getElementById('cluster-memoization')?.checked !== false,
            nodeName: document.getElementById('node-name')?.value || '',
            debugMode: document.getElementById('debug-mode')?.checked || false,
            showClickRegions: document.getElementById('show-click-regions')?.checked || false
        };
    }

    function applySettingsToApplication(settings) {
        // Apply to window settings
        if (window.electronAPI && window.electronAPI.window) {
            window.electronAPI.window.setAlwaysOnTop(settings.alwaysOnTop);
            window.electronAPI.window.setIgnoreMouseEvents(!settings.showClickRegions);
        }
        
        // Apply to Live2D manager
        if (window.angelaApp && window.angelaApp.live2dManager) {
            // 應用渲染模式設置
            if (settings.renderMode) {
                if (settings.renderMode === 'live2d' && window.angelaApp.live2dManager.getMode() === 'fallback') {
                    window.angelaApp.live2dManager.switchToLive2D();
                    console.log('[Settings] 切換到 Live2D 模式');
                } else if (settings.renderMode === 'fallback' && window.angelaApp.live2dManager.getMode() === 'live2d') {
                    window.angelaApp.live2dManager.switchToFallback();
                    console.log('[Settings] 切換到立繫模式');
                }
                // 保存到本地存儲
                localStorage.setItem('render_mode', settings.renderMode);
            }
            
            // Load selected model
            if (settings.model) {
                const modelPath = 'resources/models/' + settings.model;
                console.log('[Settings] Loading model:', settings.model, 'from', modelPath);
                window.angelaApp.live2dManager.loadModel(modelPath).then(success => {
                    if (success) {
                        console.log('[Settings] Model loaded successfully:', settings.model);
                    } else {
                        console.warn('[Settings] Failed to load model:', settings.model);
                    }
                });
            }
        }
        
        // Apply to audio handler
        if (window.angelaApp && window.angelaApp.audioHandler) {
            if (settings.continuousRecognition) {
                window.angelaApp.audioHandler.startSpeechRecognition();
            } else {
                window.angelaApp.audioHandler.stopSpeechRecognition();
            }
        }
        
        // Apply to haptic handler
        if (window.angelaApp && window.angelaApp.hapticHandler) {
            if (settings.enableHaptics) {
                window.angelaApp.hapticHandler.enable();
            } else {
                window.angelaApp.hapticHandler.disable();
            }
        }

        // Apply backend IP change
        if (window.electronAPI && window.electronAPI.backend && settings.backendIp) {
            window.electronAPI.backend.setIP(settings.backendIp);
        }
    }
});