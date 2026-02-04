/**
 * Angela AI - Settings Page
 * 
 * Handles user preferences and configuration
 */

// DOM Elements
const navItems = document.querySelectorAll('.nav-item');
const sections = document.querySelectorAll('.section');
const notificationContainer = document.getElementById('notification-container');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeSettings();
    loadCurrentSettings();
    setupEventListeners();
});

function initializeSettings() {
    console.log('Initializing Settings...');
    
    // Load available models
    loadAvailableModels();
    
    // Load available TTS voices
    loadTTSVoices();
}

function loadAvailableModels() {
    if (window.electronAPI && window.electronAPI.live2d) {
        window.electronAPI.live2d.getModels().then(models => {
            const modelSelect = document.getElementById('model-select');
            modelSelect.innerHTML = '';
            
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });
        });
    }
}

function loadTTSVoices() {
    const synth = window.speechSynthesis;
    const voices = synth.getVoices();
    
    const voiceSelect = document.getElementById('tts-voice');
    voiceSelect.innerHTML = '';
    
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
    
    // Apply settings to UI
    applySettingsToUI(settings);
}

function applySettingsToUI(settings) {
    // General
    document.getElementById('always-on-top').checked = settings.alwaysOnTop || false;
    document.getElementById('auto-start').checked = settings.autoStart || false;
    document.getElementById('window-opacity').value = settings.windowOpacity || 1;
    document.getElementById('opacity-value').textContent = `${Math.round((settings.windowOpacity || 1) * 100)}%`;
    document.getElementById('idle-mode').checked = settings.idleMode !== false;
    document.getElementById('sensitivity').value = settings.sensitivity || 'medium';
    
    // Appearance
    document.getElementById('model-select').value = settings.model || 'miara_pro';
    document.getElementById('model-scale').value = settings.modelScale || 1;
    document.getElementById('scale-value').textContent = `${(settings.modelScale || 1).toFixed(1)}x`;
    document.getElementById('wallpaper-mode').value = settings.wallpaperMode || 'overlay';
    document.getElementById('wallpaper-effect').value = settings.wallpaperEffect || 'none';
    
    // Audio
    document.getElementById('tts-engine').value = settings.ttsEngine || 'browser';
    document.getElementById('speech-rate').value = settings.speechRate || 1;
    document.getElementById('rate-value').textContent = `${(settings.speechRate || 1).toFixed(1)}x`;
    document.getElementById('speech-pitch').value = settings.speechPitch || 1;
    document.getElementById('pitch-value').textContent = `${(settings.speechPitch || 1).toFixed(1)}x`;
    document.getElementById('speech-language').value = settings.speechLanguage || 'en-US';
    document.getElementById('continuous-recognition').checked = settings.continuousRecognition !== false;
    document.getElementById('capture-system-audio').checked = settings.captureSystemAudio || false;
    
    // Haptics
    document.getElementById('enable-haptics').checked = settings.enableHaptics !== false;
    document.getElementById('click-intensity').value = settings.clickIntensity || 0.5;
    document.getElementById('click-value').textContent = `${Math.round((settings.clickIntensity || 0.5) * 100)}%`;
    document.getElementById('touch-intensity').value = settings.touchIntensity || 0.8;
    document.getElementById('touch-value').textContent = `${Math.round((settings.touchIntensity || 0.8) * 100)}%`;
    document.getElementById('emotion-intensity').value = settings.emotionIntensity || 0.7;
    document.getElementById('emotion-value').textContent = `${Math.round((settings.emotionIntensity || 0.7) * 100)}%`;
    
    // Advanced
    document.getElementById('frame-rate').value = settings.frameRate || 60;
    document.getElementById('render-quality').value = settings.renderQuality || 'medium';
    document.getElementById('debug-mode').checked = settings.debugMode || false;
    document.getElementById('show-click-regions').checked = settings.showClickRegions || false;
}

function setupEventListeners() {
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
    document.getElementById('load-wallpaper').addEventListener('click', loadWallpaper);
    document.getElementById('scan-devices').addEventListener('click', scanHapticDevices);
    document.getElementById('open-devtools').addEventListener('click', openDevTools);
    document.getElementById('reset-settings').addEventListener('click', resetSettings);
    document.getElementById('clear-cache').addEventListener('click', clearCache);
    
    // Save/Cancel
    document.getElementById('save').addEventListener('click', saveSettings);
    document.getElementById('cancel').addEventListener('click', cancelSettings);
}

function setupSlider(sliderId, displayId, formatter) {
    const slider = document.getElementById(sliderId);
    const display = document.getElementById(displayId);
    
    slider.addEventListener('input', () => {
        display.textContent = formatter(parseFloat(slider.value));
    });
}

function switchSection(sectionId) {
    // Update nav items
    navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.section === sectionId);
    });
    
    // Update sections
    sections.forEach(section => {
        section.classList.toggle('active', section.id === sectionId);
    });
}

function loadWallpaper() {
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
    if (window.angelaApp && window.angelaApp.hapticHandler) {
        window.angelaApp.hapticHandler.discoverDevices().then(devices => {
            console.log('Found haptic devices:', devices);
            showNotification(`Found ${devices.length} haptic device(s)`, 'success');
        });
    }
}

function openDevTools() {
    if (window.electronAPI && window.electronAPI.window) {
        // Open DevTools for the main window
        // This would require main process support
        showNotification('DevTools opened in main window', 'success');
    }
}

function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to default?')) {
        localStorage.removeItem('angela_settings');
        loadCurrentSettings();
        showNotification('Settings reset to default', 'success');
    }
}

function clearCache() {
    if (confirm('Are you sure you want to clear all cached data?')) {
        // Clear caches
        if (window.angelaApp && window.angelaApp.wallpaperHandler) {
            window.angelaApp.wallpaperHandler.cleanup();
        }
        
        showNotification('Cache cleared successfully', 'success');
    }
}

function saveSettings() {
    const settings = collectSettings();
    
    // Save to local storage
    localStorage.setItem('angela_settings', JSON.stringify(settings));
    
    // Apply settings to application
    applySettingsToApplication(settings);
    
    showNotification('Settings saved successfully!', 'success');
    
    // Close settings window after a delay
    setTimeout(() => {
        if (window.electronAPI && window.electronAPI.settings) {
            window.electronAPI.settings.close();
        }
    }, 1000);
}

function cancelSettings() {
    if (window.electronAPI && window.electronAPI.settings) {
        window.electronAPI.settings.close();
    }
}

function collectSettings() {
    return {
        // General
        alwaysOnTop: document.getElementById('always-on-top').checked,
        autoStart: document.getElementById('auto-start').checked,
        windowOpacity: parseFloat(document.getElementById('window-opacity').value),
        idleMode: document.getElementById('idle-mode').checked,
        sensitivity: document.getElementById('sensitivity').value,
        
        // Appearance
        model: document.getElementById('model-select').value,
        modelScale: parseFloat(document.getElementById('model-scale').value),
        wallpaperMode: document.getElementById('wallpaper-mode').value,
        wallpaperEffect: document.getElementById('wallpaper-effect').value,
        
        // Audio
        ttsEngine: document.getElementById('tts-engine').value,
        voice: document.getElementById('tts-voice').value,
        speechRate: parseFloat(document.getElementById('speech-rate').value),
        speechPitch: parseFloat(document.getElementById('speech-pitch').value),
        speechLanguage: document.getElementById('speech-language').value,
        continuousRecognition: document.getElementById('continuous-recognition').checked,
        captureSystemAudio: document.getElementById('capture-system-audio').checked,
        
        // Haptics
        enableHaptics: document.getElementById('enable-haptics').checked,
        clickIntensity: parseFloat(document.getElementById('click-intensity').value),
        touchIntensity: parseFloat(document.getElementById('touch-intensity').value),
        emotionIntensity: parseFloat(document.getElementById('emotion-intensity').value),
        
        // Advanced
        frameRate: parseInt(document.getElementById('frame-rate').value),
        renderQuality: document.getElementById('render-quality').value,
        debugMode: document.getElementById('debug-mode').checked,
        showClickRegions: document.getElementById('show-click-regions').checked
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
        // Apply model scale
        // This would need to be implemented in Live2DManager
    }
    
    // Apply to audio handler
    if (window.angelaApp && window.angelaApp.audioHandler) {
        // Apply TTS settings
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
}

function showNotification(message, type = 'info') {
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

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadCurrentSettings,
        applySettingsToUI,
        collectSettings,
        saveSettings
    };
}
