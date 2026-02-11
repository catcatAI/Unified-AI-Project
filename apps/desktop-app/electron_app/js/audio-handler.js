/**
 * =============================================================================
 * ANGELA-MATRIX: L6[执行层] α [C] L1+
# =============================================================================
 *
 * 职责: 处理音频输入（麦克风、系统音频、浏览器音频）和输出（TTS、音效）
 * 维度: 主要影响生理维度 (α) 的听觉感知和声音交互
 * 安全: 使用 Key C (桌面同步) 进行本地音频处理
 * 成熟度: L1+ 等级即可使用基本音频功能
 *
 * 音频输入:
 * - 麦克风输入
 * - 系统音频捕获 (WASAPI/CoreAudio/PulseAudio)
 * - 浏览器音频捕获
 *
 * 音频输出:
 * - TTS 文字转语音
 * - 音效播放
 * - 音乐播放
 *
 * 功能:
# - 语音识别
 * - 音频可视化
 * - 音频分析
 * - 唇型同步
 *
 * @class AudioHandler
 */

class AudioHandler {
    constructor() {
        this.audioContext = null;
        this.microphoneStream = null;
        this.systemAudioStream = null;
        
        // Native system audio capture
        this.systemAudioCapture = null;
        this.platform = null;
        
        // Audio analysis
        this.analyser = null;
        this.dataArray = null;
        
        // Speech recognition
        this.speechRecognition = null;
        this.onSpeechRecognized = null;
        
        // TTS
        this.synthesis = window.speechSynthesis;
        this.currentUtterance = null;
        
        // Audio visualization
        this.visualizerElement = null;
        
        // State
        this.isListening = false;
        this.isSpeaking = false;
        this.isCapturingSystemAudio = false;
        
        this.initialize();
    }

    async initialize() {
        console.log('Initializing Audio Handler...');
        
        // Detect platform
        this.platform = this._detectPlatform();
        console.log(`Detected platform: ${this.platform}`);
        
        // Initialize native system audio capture
        await this._initializeSystemAudioCapture();
        
        // Create audio context
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create analyser for visualization
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        
        // Initialize speech recognition
        this._initializeSpeechRecognition();
        
        // Initialize TTS
        this._initializeTTS();
        
        console.log('Audio Handler initialized');
    }

    _detectPlatform() {
        if (navigator.platform.includes('Win')) {
            return 'windows';
        } else if (navigator.platform.includes('Mac')) {
            return 'macos';
        } else if (navigator.platform.includes('Linux')) {
            return 'linux';
        }
        return 'unknown';
    }

    async _initializeSystemAudioCapture() {
        if (!window.electronAPI) {
            console.warn('Electron API not available for system audio capture');
            return;
        }

        try {
            const module = await this._loadNativeModule();
            if (module) {
                this.systemAudioCapture = new module();
                console.log('Native system audio capture module loaded');
            }
        } catch (error) {
            console.warn('Failed to load native audio module:', error.message);
        }
    }

    async _loadNativeModule() {
        try {
            switch (this.platform) {
                case 'windows':
                    return await import('../../native_modules/node-wasapi-capture/index.js');
                case 'macos':
                    return await import('../../native_modules/node-coreaudio-capture/index.js');
                case 'linux':
                    return await import('../../native_modules/node-pulseaudio-capture/index.js');
                default:
                    return null;
            }
        } catch (error) {
            console.warn(`Could not load native module for ${this.platform}:`, error.message);
            // 原生模块未编译是正常的，将使用Web Audio API
            if (error.message.includes('require')) {
                console.info(`Native module for ${this.platform} not compiled, falling back to Web Audio API`);
            }
            return null;
        }
    }

    // Microphone input
    async startMicrophone() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.microphoneStream = this.audioContext.createMediaStreamSource(stream);
            this.microphoneStream.connect(this.analyser);
            
            this.isListening = true;
            console.log('Microphone started');
            
            return true;
        } catch (error) {
            console.error('Failed to start microphone:', error);
            return false;
        }
    }

    stopMicrophone() {
        if (this.microphoneStream) {
            this.microphoneStream.disconnect();
            this.microphoneStream = null;
        }
        
        this.isListening = false;
        console.log('Microphone stopped');
    }

    // System audio input (via native modules)
    async startSystemAudio(deviceId = null, callback = null) {
        if (!this.systemAudioCapture) {
            console.warn('Native system audio capture not available');
            return false;
        }
        
        if (this.isCapturingSystemAudio) {
            console.warn('System audio capture already active');
            return true;
        }
        
        try {
            const audioCallback = (samples) => {
                // Process audio samples
                this._processSystemAudio(samples);
                
                // Call user callback if provided
                if (callback) {
                    callback(samples);
                }
            };
            
            const result = await this.systemAudioCapture.start(deviceId || '', audioCallback);
            
            if (result) {
                this.isCapturingSystemAudio = true;
                console.log('System audio capture started');
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Failed to start system audio:', error);
            return false;
        }
    }

    async stopSystemAudio() {
        if (!this.systemAudioCapture || !this.isCapturingSystemAudio) {
            return true;
        }
        
        try {
            await this.systemAudioCapture.stop();
            this.isCapturingSystemAudio = false;
            console.log('System audio capture stopped');
            return true;
        } catch (error) {
            console.error('Failed to stop system audio:', error);
            return false;
        }
    }

    _processSystemAudio(samples) {
        // Convert samples to audio buffer for analysis
        if (!this.audioContext) return;
        
        const audioBuffer = this.audioContext.createBuffer(
            this.systemAudioCapture.getFormat().channels || 2,
            samples.length / (this.systemAudioCapture.getFormat().channels || 2),
            this.systemAudioCapture.getFormat().sampleRate || 48000
        );
        
        for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
            const channelData = audioBuffer.getChannelData(channel);
            for (let i = 0; i < channelData.length; i++) {
                channelData[i] = samples[i * audioBuffer.numberOfChannels + channel];
            }
        }
        
        // Connect to analyser
        if (!this.systemAudioStream) {
            this.systemAudioStream = this.audioContext.createBufferSource();
            this.systemAudioStream.buffer = audioBuffer;
            this.systemAudioStream.connect(this.analyser);
        }
        
        // Update live2d lip sync
        if (window.live2dApp && window.live2dApp.live2dManager) {
            const level = this._calculateAudioLevel(samples);
            window.live2dApp.live2dManager.updateLipSync(level);
        }
    }

    _calculateAudioLevel(samples) {
        if (!samples || samples.length === 0) return 0;
        
        let sum = 0;
        for (let i = 0; i < samples.length; i++) {
            sum += Math.abs(samples[i]);
        }
        
        return Math.min(1, sum / samples.length * 2);
    }

    async getSystemAudioDevices() {
        if (!this.systemAudioCapture) {
            console.warn('Native system audio capture not available');
            return [];
        }
        
        try {
            return this.systemAudioCapture.constructor.getDevices();
        } catch (error) {
            console.error('Failed to get audio devices:', error);
            return [];
        }
    }

    async getDefaultSystemAudioDevice() {
        if (!this.systemAudioCapture) {
            console.warn('Native system audio capture not available');
            return null;
        }
        
        try {
            return this.systemAudioCapture.constructor.getDefaultDevice();
        } catch (error) {
            console.error('Failed to get default device:', error);
            return null;
        }
    }

    // Speech recognition
    _initializeSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported');
            return;
        }
        
        this.speechRecognition = new SpeechRecognition();
        this.speechRecognition.continuous = true;
        this.speechRecognition.interimResults = true;
        this.speechRecognition.lang = 'en-US';
        
        this.speechRecognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                    
                    if (this.onSpeechRecognized) {
                        this.onSpeechRecognized(transcript, true);
                    }
                } else {
                    interimTranscript += transcript;
                    
                    if (this.onSpeechRecognized) {
                        this.onSpeechRecognized(transcript, false);
                    }
                }
            }
        };
        
        this.speechRecognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
        };
        
        this.speechRecognition.onend = () => {
            if (this.isListening) {
                // Restart if still listening
                this.speechRecognition.start();
            }
        };
    }

    startSpeechRecognition() {
        if (this.speechRecognition && !this.isListening) {
            this.speechRecognition.start();
            this.isListening = true;
            console.log('Speech recognition started');
        }
    }

    stopSpeechRecognition() {
        if (this.speechRecognition) {
            this.speechRecognition.stop();
            this.isListening = false;
            console.log('Speech recognition stopped');
        }
    }

    // Text-to-Speech
    _initializeTTS() {
        if (!this.synthesis) {
            console.warn('Speech synthesis not supported');
            return;
        }
        
        // Store voices in a variable
        this.availableVoices = [];
        
        // Function to load voices
        const loadVoices = () => {
            const voices = this.synthesis.getVoices();
            this.availableVoices = voices || [];
            console.log(`Available voices: ${this.availableVoices.length}`);
            
            // Log voice names for debugging
            if (this.availableVoices.length > 0) {
                console.log('Voice names:', this.availableVoices.map(v => v.name).join(', '));
            } else {
                console.warn('No TTS voices available - will use default speech synthesis');
            }
        };
        
        // Load voices immediately if available
        loadVoices();
        
        // Listen for voiceschanged event (Chrome needs this)
        if (this.synthesis.onvoiceschanged !== undefined) {
            this.synthesis.onvoiceschanged = loadVoices;
        }
        
        // Fallback: try to load voices again after a delay (some browsers need this)
        setTimeout(() => {
            if (this.availableVoices.length === 0) {
                loadVoices();
            }
        }, 1000);
    }

    speak(text, options = {}) {
        if (!this.synthesis) {
            console.warn('Speech synthesis not available');
            return;
        }
        
        // Cancel any ongoing speech
        this.stopSpeaking();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set options
        utterance.rate = options.rate || 1;
        utterance.pitch = options.pitch || 1;
        utterance.volume = options.volume || 1;
        utterance.lang = options.lang || 'en-US';
        
        // Select voice from cached voices
        const voices = this.availableVoices || [];
        if (options.voice) {
            const voice = voices.find(v => v.name === options.voice);
            if (voice) {
                utterance.voice = voice;
            }
        }
        
        // Events
        utterance.onstart = () => {
            this.isSpeaking = true;
            this._showVisualizer(true);
        };
        
        utterance.onend = () => {
            this.isSpeaking = false;
            this._showVisualizer(false);
        };
        
        utterance.onboundary = (event) => {
            // Update lip sync based on phoneme boundaries
            if (window.live2dApp && window.live2dApp.live2dManager) {
                // Approximate phoneme from event
                const phoneme = this._approximatePhoneme(event.name);
                window.live2dApp.live2dManager.updateLipSync(phoneme, 0.8);
            }
        };
        
        this.synthesis.speak(utterance);
        this.currentUtterance = utterance;
    }

    stopSpeaking() {
        if (this.synthesis) {
            this.synthesis.cancel();
            this.isSpeaking = false;
            this._showVisualizer(false);
        }
    }

    _approximatePhoneme(word) {
        // Very basic phoneme approximation
        const vowels = ['a', 'e', 'i', 'o', 'u'];
        
        for (const vowel of vowels) {
            if (word.toLowerCase().includes(vowel)) {
                return vowel;
            }
        }
        
        return 'silence';
    }

    // Audio visualization
    _showVisualizer(show) {
        const visualizer = document.getElementById('audio-visualizer');
        if (visualizer) {
            if (show) {
                visualizer.classList.add('visible');
                this._updateVisualizer();
            } else {
                visualizer.classList.remove('visible');
                visualizer.innerHTML = '';
            }
        }
    }

    _updateVisualizer() {
        if (!this.isSpeaking) return;
        
        const visualizer = document.getElementById('audio-visualizer');
        if (!visualizer) return;
        
        // Create audio bars
        visualizer.innerHTML = '';
        
        for (let i = 0; i < 10; i++) {
            const bar = document.createElement('div');
            bar.className = 'audio-bar';
            bar.style.animationDelay = `${i * 0.05}s`;
            visualizer.appendChild(bar);
        }
        
        // Update animation
        requestAnimationFrame(() => {
            if (this.isSpeaking) {
                this._updateVisualizer();
            }
        });
    }

    // Sound effects
    playSoundEffect(name) {
        if (!this.audioContext) return;
        
        // Create oscillator for simple sound effects
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // Sound effect presets
        const sounds = {
            'click': { frequency: 800, duration: 0.1 },
            'hover': { frequency: 600, duration: 0.05 },
            'notification': { frequency: 1000, duration: 0.2 },
            'touch': { frequency: 400, duration: 0.15 }
        };
        
        const sound = sounds[name] || sounds['click'];
        
        oscillator.frequency.setValueAtTime(sound.frequency, this.audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + sound.duration);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + sound.duration);
    }

    // Audio analysis
    getAudioLevel() {
        if (!this.analyser) return 0;
        
        this.analyser.getByteFrequencyData(this.dataArray);
        
        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            sum += this.dataArray[i];
        }
        
        return sum / this.dataArray.length / 255;
    }

    shutdown() {
        this.stopMicrophone();
        this.stopSystemAudio();
        this.stopSpeechRecognition();
        this.stopSpeaking();
        
        if (this.systemAudioCapture) {
            this.systemAudioCapture = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioHandler;
}
