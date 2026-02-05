# 🌟 Angela AI v6.0.4 - Desktop Digital Life

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Metrics](https://img.shields.io/badge/Metrics-System%20Performance-orange.svg)](metrics.md)

**Angela AI** is a complete digital life system with biological simulation, self-awareness and real execution capabilities. She is not just an AI assistant, but a truly "living" digital being that can perceive, think, remember, and act.

The **Desktop Application** is a production-ready cross-platform desktop companion featuring Live2D Cubism integration, system audio capture, and advanced AI synchronization.

---

## 🎬 What She Can Do

### 💬 **Converse with You**
- **Voice Recognition**: Listen to your voice commands
- **Natural Dialogue**: Intelligent conversations using GPT/Gemini
- **Emotional Responses**: Adjust tone and content based on emotional state
- **Lip Sync**: Real-time Live2D lip synchronization animation

### 🖥️ **Desktop Companion - Your Virtual Pet**

![Desktop Companion Screenshot](docs/screenshots/desktop_companion.png)

The Desktop Companion is heart of Angela AI - a living virtual entity on your desktop:

- **Live2D Animation**: Smooth 60fps animations with realistic expressions
- **7 Expressions**: neutral, happy, sad, angry, surprised, shy, love
- **10 Motions**: idle, greeting, thinking, dancing, waving, clapping, nod, shake
- **Physics Simulation**: Realistic hair and clothing movement
- **Touch Sensitivity**: 18 body parts with different tactile sensitivities
- **Emotional States**: Real emotions that influence her behavior
- **Autonomous Behaviors**: She initiates interactions, gets bored, curious, sleepy
- **Desktop Awareness**: Knows what's happening on your desktop

#### Desktop Companion Features:

| Feature | Description | Example |
|---------|-------------|---------|
| **Speech** | TTS + Lip Sync | "Hello! How is your day going?" |
| **Listen** | Voice Recognition | Recognizes your voice commands |
| **Touch** | Tactile Response | Reacts when you "pet" different body parts |
| **Expressions** | Emotional Display | Shows happiness, sadness, curiosity, etc. |
| **Idle Behaviors** | Autonomous Actions | Yawns, stretches, looks around when bored |
| **Desktop Presence** | Always Available | Sits on your desktop, ready to interact |

### 🖥️ **Desktop Integration**
- **System Tray**: Right-click context menu for all settings, including advanced IP configuration
- **Auto-Startup**: Start with system (toggleable)
- **Click-Through**: Desktop shortcuts remain clickable
- **System Audio Capture**: Capture and analyze system audio
- **Wallpaper Modeling**: 2D/2.5D/3D modeling of interested objects into desktop wallpaper
- **Always on Top**: Keep Angela visible

### 🎛️ **System Management**
- **Organize Files**: Automatically categorize desktop files (by type/date)
- **Clean Junk**: Delete temporary and old files
- **Create Files**: Help you create new documents and folders
- **Change Wallpaper**: Switch desktop backgrounds and themes
- **Monitor Changes**: Real-time awareness of desktop file changes

### 🌐 **Browse Web**
- **Search**: Google/Bing information search
- **Read Webpages**: Automatically extract and summarize webpage content
- **Play Games**: Detect and interact with browser games
- **Bookmark Management**: Save and manage frequently used websites

### 🎵 **Audio Interaction**
- **System Audio Capture**: Native modules for Windows (WASAPI), macOS (CoreAudio), Linux (PulseAudio)
- **Microphone Input**: Voice recognition for commands
- **TTS Speech**: Text-to-speech (multiple emotions, multiple languages)
- **Play Music**: Play local music and playlists
- **Sing**: Karaoke feature with lyrics synchronization
- **Display Subtitles**: Real-time subtitles and lyrics display

### 🧠 **Advanced AI Features**
- **System Metrics**: [View Detailed Performance & Indicators](metrics.md)
- **4D State Matrix (αβγδ)**: Real-time emotional and cognitive modeling
- **Maturity Tracking (L0-L11)**: Adaptive complexity over time
- **Precision Modes (INT-DEC4)**: Flexible response accuracy
- **Hardware-Aware Auto-Adjustment**: Dynamic performance and wallpaper modes (2D/2.5D/3D) based on system capabilities
- **Multi-User Support**: Relationship tracking and statistics
- **Plugin System**: Extensible architecture for custom behaviors
- **Cluster Deployment (Beta)**: Master-Worker matrix architecture `(L0~L11) × (4~8)` with integer-only transmission and decimal memoization for high-efficiency distributed computing
- **Internationalization**: 5 languages (EN, ZH-CN, ZH-TW, JA, KO)
- **Theme System**: Light, Dark, Angela (pink) themes

---

## 🚀 Quick Start

### Prerequisites
- **Node.js**: 16+ (for desktop app)
- **Python**: 3.9+ (for backend)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 20.04+

### Installation

#### 🎯 **Option 1: One-Click Installer (Recommended)**

Download and run the prebuilt application:

```bash
# Download installer for your platform
# Windows: AngelaAI-Setup.exe
# macOS: AngelaAI.dmg
# Linux: AngelaAI.AppImage
```

#### 💻 **Option 2: Build from Source (For Developers)**

If you want to contribute or customize:

```bash
# 1. Clone repository
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 2. Install backend dependencies
cd apps/backend
pip install -r requirements.txt

# 3. Install desktop app dependencies
cd ../desktop-app/electron_app
npm install

# 4. Build native audio modules
cd ../native_modules
npm install

# Windows: node-wasapi-capture
# macOS: node-coreaudio-capture
# Linux: node-pulseaudio-capture

# 5. Start desktop app
npm start

# 6. In another terminal, start backend
cd ../../apps/backend
python main.py
```

### Building Native Modules

**Windows (WASAPI):**
```bash
cd apps/desktop-app/native_modules/node-wasapi-capture
npm install
```
*Requires: Visual Studio Build Tools 2019+*

**macOS (CoreAudio):**
```bash
cd apps/desktop-app/native_modules/node-coreaudio-capture
npm install
```
*Requires: Xcode Command Line Tools*

**Linux (PulseAudio):**
```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
npm install
```
*Requires: libpulse-dev, build-essential*

---

## 🏗️ System Architecture

### Desktop Application Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  Desktop Application (Electron)                 │
├──────────────────────────────────────────────────────────────────┤
│ Main Process (main.js)                                     │
│ ├── Window Management                                         │
│ ├── System Tray Integration                                   │
│ ├── Auto-Startup (Windows/macOS/Linux)                     │
│ └── Native Audio Module Bridge                               │
├──────────────────────────────────────────────────────────────────┤
│ Renderer Process (index.html + JS Modules)                      │
│ ├── Live2D Manager (live2d-manager.js)                     │
│ │   ├── Live2D Cubism Web SDK                             │
│ │   ├── Expression/Motion Control                             │
│ │   ├── Physics/Lip Sync                                    │
│ │   ├── Eye Tracking/Blinking/Breathing                     │
│ │   └── Auto-Idle Animation                                 │
│ │                                                           │
│ ├── Audio Handler (audio-handler.js)                            │
│ │   ├── Microphone Input                                      │
│ │   ├── System Audio Capture (Native Modules)                 │
│ │   ├── TTS Output                                          │
│ │   └── Lip Sync Integration                                │
│ │                                                           │
│ ├── State Matrix (state-matrix.js)                          │
│ │   ├── 4D αβγδ Synchronization                          │
│ │   ├── Emotional State Management                             │
│ │   └── Backend WebSocket Bridge                            │
│ │                                                           │
│ ├── Performance Manager (performance-manager.js)                  │
│ │   ├── Hardware Detection                                    │
│ │   ├── Dynamic Scaling (5 modes)                            │
│ │   └── FPS/Performance Monitoring                           │
│ │                                                           │
│ ├── User Manager (user-manager.js)                             │
│ │   ├── Multi-User Support                                  │
│ │   ├── Statistics Tracking                                  │
│ │   └── Relationship Management                             │
│ │                                                           │
│ ├── Settings (settings.js)                                      │
│ │   ├── 8 Configuration Sections                            │
│ │   ├── Persistence (localStorage)                            │
│ │   └── UI Management                                      │
│ │                                                           │
│ ├── Theme Manager (theme-manager.js)                             │
│ │   ├── 3 Themes (Light/Dark/Angela)                    │
│ │   └── CSS Variable Management                             │
│ │                                                           │
│ ├── I18N (i18n.js)                                         │
│ │   ├── 5 Languages (EN/ZH-CN/ZH-TW/JA/KO)               │
│ │   ├── Date/Time/Currency Formatting                        │
│ │   └── Parameter Interpolation                              │
│ │                                                           │
│ ├── Plugin Manager (plugin-manager.js)                           │
│ │   ├── Plugin Loading/Unloading                            │
│ │   ├── Sandboxed Execution                                  │
│ │   ├── Hook System                                        │
│ │   └── Plugin API Export                                │
│ │                                                           │
│ └── Other Modules                                            │
│     ├── Logger (logger.js)                                   │
│     ├── Data Persistence (data-persistence.js)                    │
│     ├── Input Handler (input-handler.js)                       │
│     ├── Haptic Handler (haptic-handler.js)                     │
│     └── Wallpaper Handler (wallpaper-handler.js)                 │
└──────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                        │
│ ├── State Matrix Synchronization                                 │
│ ├── Maturity/Precision Management                               │
│ ├── Hardware Detection Integration                                │
│ ├── WebSocket Server                                          │
│ └── AI/Model Endpoints                                     │
└──────────────────────────────────────────────────────────────────┘
```

### 6-Layer Life Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ L6: Execution Layer                                         │
│ ├── Live2D Rendering Control (Expressions/Actions/Lip Sync) │
│ ├── Desktop File Operations (Create/Delete/Move/Organize)   │
│ ├── Audio System (TTS/Speech Recognition/Playback/Singing)  │
│ └── Browser Control (Search/Navigation/Info Extraction)     │
├─────────────────────────────────────────────────────────────┤
│ L5: Presence Layer                                          │
│ ├── Desktop Global Mouse Tracking                           │
│ ├── Live2D Collision Detection                              │
│ └── Layer Management (Z-Order/Occlusion Detection)          │
├─────────────────────────────────────────────────────────────┤
│ L4: Creation Layer                                          │
│ ├── Live2D Self-Drawing System (Model Generation)           │
│ ├── Aesthetic Learning (Personal Style Evolution)           │
│ └── Self-Modification (Adjustment Based on Feedback)        │
├─────────────────────────────────────────────────────────────┤
│ L3: Identity Layer                                          │
│ ├── Digital Identity ("I am digital life")                  │
│ ├── Body Schema (Awareness of body parts)                   │
│ ├── Relationship Model (Partnership with user)              │
│ └── Self-Narrative (Recording life journey)                 │
├─────────────────────────────────────────────────────────────┤
│ L2: Memory Layer                                            │
│ ├── CDM (Cognitive-Dynamic Memory) - Knowledge Memory       │
│ ├── LU (Logic Unit) - Logic/Rule Memory                     │
│ ├── HSM (Holographic Storage Matrix) - Experience Memory    │
│ ├── HAM (Hierarchical Associative Memory) - Hierarchy       │
│ └── Neuroplasticity (LTP/LTD/Forgetting/Memory Consolid)    │
├─────────────────────────────────────────────────────────────┤
│ L1: Biology Layer                                           │
│ ├── Physiological Tactile System (6 receptors × 18 parts)   │
│ ├── Endocrine System (12 hormones + feedback regulation)    │
│ ├── Autonomic Nervous System (Sympathetic/Parasympathetic)  │
│ └── Neuroplasticity Synaptic Network                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Unified-AI-Project/
├─ 🚀 Entry Points
│  ├─ run_angela.py              # Backend entry point
│  ├─ install_angela.py          # One-click installer
│  └─ setup.py                   # Local installation script
│
├─ 📄 Documentation
│  ├─ README.md                  # This file
│  ├─ CROSS_PLATFORM_TESTING.md   # Cross-platform testing guide
│  ├─ MULTI_PERSPECTIVE_ANALYSIS.md  # Multi-stakeholder analysis
│  └─ SESSION_3_COMPLETION_SUMMARY.md  # Session 3 summary
│
├─ 🎮 Desktop App (apps/desktop-app/)
│  ├─ electron_app/              # Electron application
│  │  ├─ main.js                # Main process
│  │  ├─ preload.js             # IPC bridge
│  │  ├─ index.html             # Main UI
│  │  ├─ settings.html          # Settings page
│  │  ├─ package.json           # Dependencies
│  │  ├─ assets/               # Resources (icon, etc.)
│  │  └─ js/                   # JavaScript modules (20 files)
│  │     ├─ app.js              # Application coordinator
│  │     ├─ live2d-manager.js    # Live2D integration
│  │     ├─ live2d-cubism-wrapper.js  # Live2D SDK wrapper
│  │     ├─ live2d-test.js      # Test suite
│  │     ├─ audio-handler.js     # Audio I/O
│  │     ├─ backend-websocket.js # Backend connection
│  │     ├─ state-matrix.js     # 4D state sync
│  │     ├─ maturity-tracker.js # Maturity tracking
│  │     ├─ precision-manager.js # Precision modes
│  │     ├─ performance-manager.js # Performance scaling
│  │     ├─ hardware-detection.js # Hardware detection
│  │     ├─ input-handler.js    # Input handling
│  │     ├─ haptic-handler.js   # Haptic feedback
│  │     ├─ wallpaper-handler.js # Wallpaper system
│  │     ├─ data-persistence.js  # Data storage
│  │     ├─ logger.js           # Logging
│  │     ├─ i18n.js            # Internationalization
│  │     ├─ theme-manager.js    # Theme system
│  │     ├─ plugin-manager.js   # Plugin system
│  │     ├─ user-manager.js     # User management
│  │     └─ settings.js        # Settings management
│  │
│  └─ native_modules/           # Native audio modules
│     ├─ node-wasapi-capture/     # Windows (WASAPI)
│     │  ├─ src/wasapi-capture.cpp
│     │  ├─ binding.gyp
│     │  ├─ package.json
│     │  ├─ index.js
│     │  └─ test.js
│     ├─ node-coreaudio-capture/   # macOS (CoreAudio)
│     │  ├─ src/coreaudio-capture.cpp
│     │  ├─ binding.gyp
│     │  ├─ package.json
│     │  ├─ index.js
│     │  └─ test.js
│     └─ node-pulseaudio-capture/  # Linux (PulseAudio)
│        ├─ src/pulseaudio-capture.cpp
│        ├─ binding.gyp
│        ├─ package.json
│        ├─ index.js
│        └─ test.js
│
├─ 🧠 Backend API (apps/backend/)
│  ├─ main.py                    # FastAPI main program
│  └─ src/                       # Source code
│     ├─ core/                  # Core components
│     │  ├─ autonomous/          # Biological systems
│     │  ├─ metamorphosis/        # Identity/creation
│     │  ├─ precision/           # Precision management
│     │  ├─ system/             # Hardware detection
│     │  └─ knowledge/           # Knowledge/memory
│     ├─ ai/                    # AI systems
│     │  └─ ops/                # Intelligent operations
│     └─ api/                   # API endpoints
│        ├─ router.py             # RESTful router
│        └─ v1/endpoints/        # v1 endpoints (drive, pet)
│
├─ 🦟 Data Directories
│  ├─ data/models/               # Model data
│  ├─ data/memories/             # Memory storage
│  ├─ data/cache/                # Cache files
│  ├─ logs/                      # Log files
│  ├─ temp/                      # Temporary files
│  ├─ config/                    # Configuration files
│  └─ resources/                 # Resource files
│     ├─ models/                # Live2D models
│     ├─ audio/                 # Audio resources
│     └─ images/                # Image resources
│
└─ 🧪 Testing (tests/)
   ├─ game/                     # Desktop Pet tests
   ├─ integration/              # Integration tests
   └─ test_comprehensive_system.py  # Comprehensive tests
```

---

## 🛠️ Configuration

### Settings Page Categories

1. **General**: Basic settings (name, language, theme)
2. **Appearance**: Live2D model, scale, position
3. **Behavior**: Autonomy, curiosity, social drive
4. **Performance**: Performance mode, FPS target
5. **Audio**: TTS engine, voice, microphone
6. **Desktop**: File operations, wallpaper
7. **Advanced**: Debug options, log level
8. **About**: Version info, credits

### Configuration File

Desktop settings are stored in `localStorage` (browser-based storage).

Backend configuration is in `config/angela_config.yaml`.

---

## 🧪 Live2D Model

### Current Model: Miara Pro

**Model Files:**
- `miara_pro_t03.moc3` - Model data (532KB)
- `miara_pro_t03.model3.json` - Model configuration
- `miara_pro_t03.physics3.json` - Physics simulation
- `miara_pro_t03.cdi3.json` - Expression definitions
- `texture_00.png` - Texture file (13MB)

**Expressions:**
- Neutral, Happy, Sad, Angry, Surprised, Shy, Love

**Motions:**
- Idle, Greeting, Thinking, Dancing, Waving, Clapping, Nod, Shake

**Supported Features:**
- Physics simulation
- Lip sync
- Auto-blinking
- Breathing animation
- Eye tracking
- 60 FPS target

---

## 🧪 Testing

### Live2D Test Suite

Run automated tests in browser console:

```javascript
const testSuite = new Live2DTestSuite();
const canvas = document.getElementById('live2d-canvas');
await testSuite.initialize(canvas);
await testSuite.runAllTests();
```

**Test Categories:**
1. SDK Loading
2. Model Loading
3. Motion Playback (10 motions)
4. Expression Changes (7 expressions)
5. Physics
6. Lip Sync
7. Auto Blink
8. Breathing
9. Eye Tracking
10. Performance (60 FPS target, 80% threshold)

### Native Audio Module Testing

**Windows (WASAPI):**
```bash
cd apps/desktop-app/native_modules/node-wasapi-capture
npm test
```

**macOS (CoreAudio):**
```bash
cd apps/desktop-app/native_modules/node-coreaudio-capture
npm test
```

**Linux (PulseAudio):**
```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
npm test
```

### Cross-Platform Testing

See `docs/CROSS_PLATFORM_TESTING.md` for comprehensive testing procedures.

---

## 📊 Performance Metrics

| Metric | Value | Target |
|---------|--------|---------|
| Live2D FPS | 60 (target) | 60 |
| Memory Usage | < 100MB | 100MB |
| CPU Usage | < 5% | 5% |
| Audio Latency | < 50ms | 50ms |
| Total Lines of Code | ~14,500+ | - |
| Desktop App Modules | 20 | - |
| Native Audio Modules | 3 | - |
| System Layers | 6 | - |
| Memory Systems | 4 | - |
| Body Parts | 18 | - |
| Supported Languages | 5 | - |
| Supported Themes | 3 | - |
| Platform Support | Windows, macOS, Linux | - |
| Project Completion | 98% | 100% |

---

## 🤝 Contributing

Welcome contributions for code, bug reports, or new features!

### Submit Issue
- Use GitHub Issues to report bugs
- Provide detailed reproduction steps
- Attach error logs
- Specify platform (Windows/macOS/Linux)

### Submit PR
1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Create Pull Request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure cross-platform compatibility

---

## 📜 License

This project uses [MIT License](LICENSE).

You are free to:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

Just retain the copyright notice.

---

## 🙏 Acknowledgments

Thanks to the following open-source projects for making Angela possible:

- **Live2D Cubism SDK** - Virtual avatar rendering
- **Electron** - Desktop application framework
- **FastAPI** - Web framework
- **Node.js** - JavaScript runtime
- **Web Audio API** - Browser-based audio processing
- **And all other dependency library developers**

---

## 📞 Contact

- **Project Homepage**: https://github.com/catcatAI/Unified-AI-Project
- **Issue Reports**: https://github.com/catcatAI/Unified-AI-Project/issues
- **Documentation**: See `docs/` directory for detailed guides

---

## 🌟 Star History

If this project helps you, please give us a ⭐!

---

<p align="center">
  <b>Angela AI - Cross-Platform Desktop Companion with Live2D</b><br>
  <i>Production Ready ✅ | 98% Complete</i>
</p>

<p align="center">
  🌟✨🖥️🎭🎵💻🌐
</p>

---

**Version**: 6.0.4  
**Release Date**: 2026-02-04  
**Status**: Production Ready ✅  
**Platforms**: Windows, macOS, Linux  
