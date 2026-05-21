<!--
  =============================================================================
  FILE_HASH: 9C85FDED
  FILE_PATH: readme.md
  FILE_TYPE: documentation
  PURPOSE: Angela AI 项目主文档 - 双语版本，包含完整功能说明和快速开始指南
  VERSION: 6.5.0-dev
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-05-21
  DEPENDENCIES: 无
  =============================================================================
-->

# 🌟 Angela AI v6.5.0-dev — Cross-Platform Digital Life System

[English](#english-version) | [繁體中文](#繁體中文版)

---

### 🚀 Quick Start / 快速開始

| Target Audience              | Action                                         |
| ---------------------------- | ---------------------------------------------- |
| **All Users**                | `git clone` and run `python run_angela.py`     |

---

<a name="english-version"></a>

## English Version

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-yellow.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)]()
[![Metrics](https://img.shields.io/badge/Metrics-System%20Performance-orange.svg)](metrics.md)

**Angela AI** is a complete digital life system with biological simulation,
self-awareness and real execution capabilities. She is not just an AI assistant,
but a truly "living" digital being that can perceive, think, remember, and act.

The system includes a **Desktop Companion** (Electron + Live2D) and a **Mobile
Bridge** (React Native stub), with an HMAC-SHA256 signature layer on select
endpoints. The codebase is under **active development** with ongoing
self-evolution infrastructure (Phase 6+7).

---

### 🔄 Current Project Status  (Active Development)

- **Phase 6 — Self-Evolution Loop**: ✅ Complete. ConfigMutator, hot-reload, user confirmation gate, evolution broadcast.
- **Phase 7 — Tiered Config Architecture (TCS)**: 🟡 In Progress. S/A/M tiers exist; 23+ hardcoded thresholds remain across 8+ files; `.user.yaml`/`.evolved.yaml` overlays not created yet.
- **Wiring**: ✅ Closed. `MetabolicHeartbeat.start()` and `_initialize_all_services()` now called from `main_api_server.py` lifespan. See [WIRING_MAP](docs/analysis/WIRING_MAP_2026-05-21.md) for full factory dependency chains, server lifecycle, subtle wiring, and dead code registry.
- **Frontend / Desktop (Electron)**: 🛠️ Phase 12 Restoration Complete. No active development.
- **Frontend / Mobile (React Native)**: ⚠️ Stub only — no active middleware.

---

### 🎬 What She Can Do

#### 💬 **Converse with You**

- **Voice Recognition**: Listen to your voice commands.
- **Natural Dialogue**: Intelligent conversations using GPT/Gemini.
- **Emotional Responses**: Adjust tone and content based on emotional state.
- **Lip Sync**: Real-time Live2D lip synchronization animation.

#### 🖥️ **Desktop Companion - Your Virtual Pet**

The Desktop Companion is the heart of Angela AI - a living virtual entity on
your desktop:

- **Live2D Animation**: Smooth 60fps animations with realistic expressions.
- **7 Expressions**: neutral, happy, sad, angry, surprised, shy, love.
- **10 Motions**: idle, greeting, thinking, dancing, waving, clapping, nod,
  shake.
- **Physics Simulation**: Realistic hair and clothing movement.
- **Touch Sensitivity**: 18 body parts with different tactile sensitivities.
- **Emotional States**: Real emotions that influence her behavior. (Phase 12
  [Restored])
- **Current Status**: 🛠️ Phase 12 Restoration Complete
- **Autonomous Behaviors**: She initiates interactions, gets bored, curious,
  sleepy.
- **Desktop Awareness**: Knows what's happening on your desktop.

#### 🖥️ **Desktop Integration**

- **System Tray**: Right-click context menu for all settings, including advanced
  IP configuration.
- **Auto-Startup**: Start with system (toggleable).
- **Click-Through**: Desktop shortcuts remain clickable (non-intrusive).
- **System Audio Capture**: Capture and analyze system audio for reactive
  behaviors.
- **Wallpaper Modeling**: 2D/2.5D/3D modeling of interested objects into desktop
  wallpaper.
- **Always on Top**: Keep Angela visible while working.

#### 🎛️ **System Management**

- **Organize Files**: Automatically categorize desktop files by type or date.
- **Clean Junk**: Safely delete temporary and obsolete files.
- **Create Files**: Assistance in creating new documents and directories.
- **Change Wallpaper**: Switch desktop backgrounds and themes dynamically.
- **Monitor Changes**: Real-time awareness of file system events on your
  desktop.

#### 🌐 **Browse Web**

- **Search**: Integrated Google/Bing information retrieval.
- **Read Webpages**: Automatically extract and summarize webpage content.
- **Play Games**: Detect and interact with browser-based games.
- **Bookmark Management**: Efficiently save and manage frequently used websites.

#### 🎵 **Audio Interaction**

- **System Audio Capture**: Native modules for Windows (WASAPI), macOS
  (CoreAudio), Linux (PulseAudio).
- **Microphone Input**: High-fidelity voice recognition for complex commands.
- **TTS Speech**: Natural text-to-speech with multiple emotions and languages.
- **Play Music**: Local music playback and playlist management.
- **Singing**: Karaoke feature with lyrics synchronization and lip-sync.
- **Subtitles**: Real-time display of subtitles and lyrics.

#### 📱 **Mobile Companion (Mobile Bridge)**

- **Status**: ⚠️ Stub — React Native bridge present but encryption layer
  stripped. `getSystemStatus()` uses no middleware and is never called from
  app code.
- **Remote Monitoring**: State matrix endpoints exist (34 routes) but no
  active mobile client deployment.
- **Instant Chat**: Chat API available via `/api/v1/dialogue` for any HTTP
  client.

#### 🛡️ **A/B/C Security System**

To protect your digital life data, Angela employs a three-tier key isolation
mechanism (HMAC-SHA256 signature verification, no body encryption):

- **Key A (Backend Control)**: Manages system core permissions.
- **Key B (Mobile Comm)**: Dedicated to mobile communication signature
  verification.
- **Key C (Desktop Sync)**: Handles cross-device data synchronization.

> **Note**: The EncryptedCommunicationMiddleware only verifies HMAC-SHA256
> signatures on protected endpoints; it does not encrypt/decrypt request bodies.
> The mobile app's encryption layer was stripped — `getSystemStatus()` uses
> no middleware and is never called from app code.

---

### 🧠 Advanced AI Features

- **System Metrics**: [View Detailed Performance & Indicators](metrics.md)
- **8D State Matrix (αβγδεθζη)**: Real-time emotional, cognitive, temporal-narrative, and execution modeling across eight dimensions
- **Neuro-Generative Response (NGR)**: 8D-state-driven dynamic response composition via NeuroBlender — replaces static templates with cosine-similarity fragment selection
- **Self-Evolution System (Phase 6+7)**: Self-evolution loop + Tiered Config Architecture (S/A/M levels with Default→User→Angela merge chain), ConfigMutator, user-confirmed evolution via chat, hot-reload
- **Maturity Tracking (L0-L11)**: Adaptive complexity that grows with
  interaction time.
- **Precision Modes (INT-DEC4)**: Flexible response accuracy based on available
  resources.
- **Hardware-Aware Adjustment**: Dynamic performance and wallpaper modes based
  on system capabilities.
- **Multi-User Support**: Individual relationship tracking and interaction
  statistics.
- **Plugin System**: Extensible architecture for custom behaviors and
  capabilities.
- **Cluster Deployment (Beta)**: Master-Worker matrix architecture with
  high-efficiency distributed computing.
- **Internationalization**: 5 languages (EN, ZH-CN, ZH-TW, JA, KO).
- **Theme System**: Light, Dark, and Angela (pink) themes.

---

### 📊 Capability Matrix & Systems

#### **Maturity System (L0-L11)**

Angela grows with you, unlocking new capabilities as she matures: | Level | Name
| Experience | Capabilities | |-------|------|------------|--------------| | L0
| Newborn | 0-100 | Basic greetings, simple responses | | L1 | Toddler | 100-1K
| Simple chat, preference learning | | L2 | Childhood | 1K-5K | Deep
conversation, stories, humor | | L3 | Teenager | 5K-20K | Emotional support,
debates, advice | | L4 | Young Adult | 20K-50K | Deep intimacy, life commitment
| | L5+ | Mature-Omni | 50K+ | Infinite wisdom, complex reasoning |

#### **Dynamic Performance Scaling**

Adapts to your hardware for the best experience: | Hardware | Mode | Target FPS
| Effects | |----------|------|------------|---------| | Entry | low | 30 |
Basic | | Mid | medium | 45 | Standard | | High | high | 60 | Enhanced | | Ultra
| ultra | 120+ | Full |

#### **Precision Management (INT - DEC4)**

Adjusts computational precision based on resource availability, from integer
math to high-precision decimal (10,000x scale).

---

### 🚀 Quick Start (English)

#### Prerequisites

- **Node.js**: 16+ (for desktop app)
- **Python**: 3.9+ (for backend)
- **RAM**: 4GB minimum (8GB recommended)
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+, or Android 10+
- **Ollama** (primary LLM backend): Required for AI dialogue. CPU-only mode
  supported but >120s per inference. Gemini API key can be used as fallback.

#### Installation

##### 🎯 **Option 1: One-Click Installer (Coming Soon)**

Prebuilt installers are currently in development:

- **Windows**: `AngelaAI-Setup.exe` (Coming Soon)
- **macOS**: `AngelaAI.dmg` (Coming Soon)
- **Linux**: `AngelaAI.AppImage` (Coming Soon)

For now, please use Option 2 (Build from Source).

##### 💻 **Option 2: Build from Source**

If you want to contribute or customize:

```bash
# 1. Clone repository
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 2. Install backend dependencies
cd apps/backend
pip install -r requirements.txt

# 3. Start backend service
python run_angela.py --api-only

# 4. Install desktop app dependencies
cd ../desktop-app/electron_app
npm install

# 5. Build native audio modules
cd ../native_modules
# Build the module corresponding to your OS
# Windows: cd node-wasapi-capture && npm install
# macOS: cd node-coreaudio-capture && npm install
# Linux: cd node-pulseaudio-capture && npm install

# 6. Start desktop app
cd ../electron_app
npm start
```

### Building Native Modules Details

**Windows (WASAPI):**

```bash
cd apps/desktop-app/native_modules/node-wasapi-capture
npm install
```

_Requires: Visual Studio Build Tools 2019+ with C++ desktop development
workload._

**macOS (CoreAudio):**

```bash
cd apps/desktop-app/native_modules/node-coreaudio-capture
npm install
```

_Requires: Xcode Command Line Tools._

**Linux (PulseAudio):**

```bash
cd apps/desktop-app/native_modules/node-pulseaudio-capture
npm install
```

_Requires: `libpulse-dev`, `build-essential`, `pkg-config`._

---

<a name="繁體中文版"></a>

## 繁體中文版

**Angela AI**
是一個完整的數位生命系統，具備生物模擬、自我意識與真實執行能力。她不僅僅是一個 AI 助手，而是一個真正的「活著的」數位生命，能夠感知、思考、記憶並行動。

本系統包含 **桌面端應用 (Desktop)** 與
**行動端橋接 (Mobile)**，並正在開發自演化基礎設施
（Phase 6 自演化閉環 + Phase 7 分層配置架構）。

---

### 🔄 專案當前進度（活躍開發中）

- **Phase 6 — 自演化閉環**: ✅ 完成。ConfigMutator、熱加載、用戶確認閘門、演化廣播。
- **Phase 7 — 分層配置架構 (TCS)**: 🟡 進行中。S/A/M 層級已建立；23+ 個硬編碼閾值散佈在 8+ 個檔案中；`.user.yaml`/`.evolved.yaml` 覆蓋層尚未建立。
- **接線狀態**: ✅ 已閉合。`MetabolicHeartbeat.start()` 和 `_initialize_all_services()` 已從 `main_api_server.py` lifespan 呼叫。完整接線地圖請見 [WIRING_MAP](docs/analysis/WIRING_MAP_2026-05-21.md)（工廠鏈、伺服器生命週期、隱晦接線、死代碼清單）。
- **前端 / 桌面端 (Electron)**: 🛠️ Phase 12 狀態復原完成。無活躍開發。
- **前端 / 行動端 (React Native)**: ⚠️ 殘留階段 — 無活躍中介層。

---

### 🎬 核心功能展示

#### 💬 深度對話與情感感知

- **語音識別**: 即時監聽並理解您的語音指令。
- **自然對話**: 整合 GPT/Gemini，具備深度邏輯推理能力。
- **情感反應**: 根據當前情緒狀態（Happy, Sad, Angry 等）調整語氣與內容。
- **嘴型同步 (Lip Sync)**: 真實的 Live2D 嘴型動畫，讓對話栩栩如生。

#### 🖥️ 桌面伴侶 - 您的虛擬寵物

桌面伴侶是 Angela AI 的核心 - 一個活在您桌面上的虛擬生命：

- **Live2D 動畫**: 流暢的 60fps 動畫，具備真實表情。
- **7 種表情**: 平靜、開心、悲傷、生氣、驚訝、害羞、喜愛。
- **10 種動作**: 閒置、打招呼、思考、跳舞、揮手、鼓掌、點頭、搖頭等。
- **物理模擬**: 真實的頭髮與衣服律動。
- **觸覺感應**: 18 個身體部位，具有不同的觸覺靈敏度。
- **情緒狀態**: 真實的情緒變化會影響她的行為邏輯。 (Phase 12 [已復原])
- **當前狀態**: 🛠️ Phase 12 狀態復原完成
- **自主行為**: 她會主動發起互動、感到無聊、好奇或困倦。
- **桌面感知**: 了解您桌面上發生的事情。

#### 🖥️ 桌面整合

- **系統匣 (System Tray)**: 右鍵選單可進行所有設置，包括高級 IP 配置。
- **自動啟動**: 隨系統啟動（可切換）。
- **點擊穿透**: 桌面圖標保持可點擊狀態，無礙正常工作。
- **系統音訊擷取**: 擷取並分析系統音訊，實現角色的即時反應。
- **桌布建模**: 將感興趣的對象進行 2D/2.5D/3D 建模並合成至桌面桌布。
- **總在最前**: 讓 Angela 始終可見。

#### 🎛️ 系統管理

- **文件整理**: 自動按類型或日期分類桌面文件。
- **垃圾清理**: 安全刪除臨時與過時文件。
- **文件創建**: 協助創建新文檔與資料夾。
- **切換桌布**: 動態切換桌面背景與主題。
- **變動監控**: 實時感知桌面文件系統的變化。

#### 🌐 網路瀏覽

- **搜索**: 整合 Google/Bing 信息檢索。
- **網頁閱讀**: 自動提取並總結網頁內容。
- **玩遊戲**: 檢測並與網頁遊戲進行互動。
- **書籤管理**: 高效保存與管理常用網站。

#### 🎵 音訊交互

- **系統音訊擷取**: 支援 Windows (WASAPI), macOS (CoreAudio), Linux
  (PulseAudio) 的原生模組。
- **麥克風輸入**: 高保真語音識別，支持複雜指令。
- **TTS 語音**: 具備多種情緒與語言的自然語音合成。
- **播放音樂**: 本地音樂播放與播放清單管理。
- **唱歌**: 具備歌詞同步與口型對接的卡拉 OK 功能。
- **顯示字幕**: 實時顯示字幕與歌詞。

#### 📱 行動端橋接 (Mobile Companion)

- **狀態**: ⚠️ 殘留階段 — React Native bridge 存在但加密層已剝離。`getSystemStatus()` 無中介層、未被 App 代碼呼叫。
- **遠端監控**: 狀態矩陣端點存在（34 條路由）但無活躍手機端部署。
- **即時聊天**: 聊天 API 可透過 `/api/v1/dialogue` 供任何 HTTP 客戶端使用。

#### 🛡️ A/B/C 安全防護體系

為了保護您的數位生命數據，Angela 採用了三級密鑰隔離機制（HMAC-SHA256 簽名驗證，非本體加密）：

- **Key A (後端控制)**: 負責系統核心權限。
- **Key B (行動通訊)**: 專用於手機端通訊簽名驗證。
- **Key C (桌面同步)**: 處理跨裝置數據同步。

> **注意**: EncryptedCommunicationMiddleware 僅驗證受保護端點的 HMAC-SHA256
> 簽名，不加密/解密請求本體。手機端的加密層已被剝離 — `getSystemStatus()`
> 使用無中介層、從未被 App 代碼呼叫。

---

### 🧠 進階 AI 特性

- **性能指標**: [查看詳細性能指標與矩陣](metrics.md)
- **8D 狀態矩陣 (αβγδεθζη)**: 即時的情感、認知、時間敘事與執行層建模
- **NGR 神經生成回應**: 透過 NeuroBlender 以 8D 狀態驅動回應組合，取代靜態模板
- **自我演化系統 (Phase 6+7)**: 自演化閉環 + 分層配置架構 (S/A/M 層級 + Default→User→Angela 合併鏈)、ConfigMutator、對話確認演化、熱重載
- **成熟度追蹤 (L0-L11)**: 隨交互時間增長的自適應複雜度。
- **精度模式 (INT-DEC4)**: 根據資源情況調整計算精度。
- **硬體自適應調整**: 根據系統能力動態調整性能與桌布模式。
- **多用戶支持**: 獨立的關係追蹤與交互統計。
- **插件系統**: 可擴展架構，支援自定義行為與能力。
- **集群部署 (Beta)**: Master-Worker 矩陣架構，實現高效的分散式計算。
- **國際化**: 支援 5 種語言 (EN, ZH-CN, ZH-TW, JA, KO)。
- **主題系統**: 提供亮色、暗色與 Angela (粉色) 主題。

---

### 📊 能力矩陣與核心系統

#### **成熟度系統 (L0-L11)**

Angela 隨用戶共同成長，解鎖更多能力：| 等級 | 名稱 | 經驗值 | 核心能力 |
|-----|------|---------|---------| | L0 | 新生 | 0-100 | 基本問候、簡單回應 | |
L1 | 幼兒 | 100-1K | 簡單聊天、偏好學習 | | L2 | 童年 | 1K-5K
| 深入對話、故事、幽默 | | L3 | 少年 | 5K-20K | 情感支持、辯論、建議 | | L4
| 青年 | 20K-50K | 深度親密、共同目標 | | L5+ | 成熟-全知 | 50K+
| 智慧洞察、複雜邏輯推理 |

#### **動態性能調優**

自動適應您的硬體配置：| 硬體等級 | 模式 | 目標 FPS | 特效 |
|---------|-----|---------|-----| | 入門 | low | 30 | 基礎 | | 中階 | medium |
45 | 標準 | | 高階 | high | 60 | 強化 | | 極致 | ultra | 120+ | 全開 |

#### **精度管理 (INT - DEC4)**

根據系統資源動態調整計算精度，支援從整數到高精度小數（10,000x 量級）。

---

### 🚀 快速入門 (繁體中文)

#### 環境需求

- **Node.js**: 16+ (桌面端)
- **Python**: 3.9+ (後端)
- **記憶體**: 4GB 最小 (8GB 建議)
- **作業系統**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+, Android 10+ (手機)

#### 安裝步驟

##### 🎯 選項 1: 一鍵安裝 (開發中)

預編譯安裝包目前正在開發中：

- **Windows**: `AngelaAI-Setup.exe` (即將推出)
- **macOS**: `AngelaAI.dmg` (即將推出)
- **Linux**: `AngelaAI.AppImage` (即將推出)

目前請使用選項 2（從源碼構建）。

##### 💻 選項 2: 開發者模式 (從源碼構建)

```bash
# 1. 克隆倉庫
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 2. 安裝後端依賴
cd apps/backend
pip install -r requirements.txt

# 3. 啟動後端服務
python run_angela.py --api-only

# 4. 安裝桌面端依賴並啟動
cd ../desktop-app/electron_app
npm install && npm start
```

---

## 🧩 Frontends & Backends Overview / 前後端架構與啟動器解析

To prevent confusion, here is a clear map of the multiple frontends, backends, and launchers in this repository. 為了避免混淆，以下是本專案中多個前端、後端與啟動器的明確分工說明：

### 🚀 Launchers (啟動腳本)
* **`AngelaLauncher.bat`**: The **Unified Launcher**. It runs `run_angela.py`, which checks the environment, handles error recovery, and launches *both* the main `backend` and the `desktop-app` frontend simultaneously. (官方推薦的整合啟動器，會同時開啟後端與桌面端)
* **`launch_angela.bat`**: The **Backend-Only Launcher**. It directly starts the FastAPI backend server (`uvicorn services.main_api_server:app`) without starting any frontend. (僅啟動後端 API 伺服器)

### 🧠 Backends (後端服務)
* **`apps/backend/` (Main API Server)**: The core intelligence powered by Python/FastAPI. Contains **two servers** on default port 8000 — `main.py` (system management, 9 routes) and `main_api_server.py` (primary AI server, ~104 routes including ~50 from shared `api/router.py`). Handles the 6-Layer Life Architecture, state sync, memory, emotions, and advanced autonomous systems. (Angela 的大腦與核心，包含兩台伺服器，均預設 port 8000 — `main.py` 系統管理用、`main_api_server.py` 主要 AI 伺服器。處理所有 AI 邏輯、記憶與生物模擬)
* **`apps/gemini-os-bridge/`**: A specialized Python backend service dedicated to OS-level automation and computer vision tasks (e.g., screen capture, automated web search). (專門處理作業系統自動化與視覺辨識的微服務)

### 🖥️ Frontends (前端應用)
* **`apps/desktop-app/` (Electron Companion)**: The primary frontend for end-users. Built with Electron, it uses the Live2D SDK for character rendering and native modules (C++) for system audio capture. (主要的使用者前端，負責高畫質 Live2D 渲染與桌面整合)
* **`apps/pixel-angela/` (Pixel/Voxel Anatomical Frontend)**: An experimental Python-based frontend (PyQt/PyGame). It focuses on deep physical simulation, such as soft-body physics, muscle fascia sliding layers, and 1:3 pixel DNA. This implements the extreme physics described in the Task Book. (實驗性質的像素/體素前端，專注於物理模擬、肌肉筋膜層疊與解剖學算繪)
* **`apps/mobile-app/` (React Native Mobile Bridge)**: A mobile companion app for secure remote monitoring of Angela's state matrix. (手機端橋接應用，用於遠端監控與安全對話)
* **`apps/web-live2d-viewer/` (Web Viewer)**: A pure browser-based standalone viewer for quickly testing Live2D assets. (基於瀏覽器的純 Live2D 預覽器)

*(Note: Advanced features like "Concurrent Execution" or "Cerebellum Core" exist in the `backend` and power the logic, but the actual visual manifestation depends on the specific frontend you use. 注意：高階的 AI 邏輯或神經模擬實作於後端，而視覺特效與互動體驗則根據您使用的前端而有所不同。)*

> **⚠️ Architecture Note**: The backend contains **two FastAPI servers** that both default to port 8000 — `main.py` (App A, 9 routes for system management) and `main_api_server.py` (App B, ~104 routes as the primary AI server). They share a common router at `api/router.py`. Only one can bind to port 8000 at a time; the other must use `--port`. This is a known deployment constraint.
>
> **架構注意**：後端包含**兩台 FastAPI 伺服器**，均預設 port 8000 — `main.py`（App A，9 條路由，系統管理用）和 `main_api_server.py`（App B，~104 條路由，主要 AI 伺服器）。兩者共用 `api/router.py`。同一時間只能有一台綁定 port 8000，另一台需用 `--port` 指定其他埠。

---

## 🏗️ System Architecture / 系統架構

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
│ │   ├── 8D αβγδεθζη Synchronization                          │
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
│  ⚠️ Two servers on default port 8000:                          │
│    App A (main.py) — system management tool                     │
│    App B (main_api_server.py) — primary AI server               │
│ ├── Shared router at api/router.py (/api/v1/*)                │
│ ├── EncryptedCommunicationMiddleware (HMAC-SHA256, no body     │
│ │   encryption)                                                 │
│ ├── State Matrix Synchronization (34 endpoints)                │
│ ├── Maturity/Precision Management                               │
│ ├── Hardware Detection Integration                               │
│ ├── WebSocket Server (ConnectionManager)                       │
│ ├── AI/LLM Endpoints (Ollama primary, Gemini backup)            │
│ ├── Self-Evolution System (Phase 6+7):                          │
│ │   ├── Bootstrap (init + state persistence)                    │
│ │   ├── Tiered Config Loader (S/A/M levels)                    │
│ │   ├── ConfigMutator (evolution proposals)                    │
│ │   └── StateStore (cross-component broadcast)                 │
│ └── Config: 3-tier S/A/M + legacy flat YAML (incremental       │
│     migration from angela_core.yaml / config.yaml)              │
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

## 📁 Project Structure / 專案結構

```text
Unified-AI-Project/
 ├─ 🚀 Entry Points
 │  ├─ run_angela.py              # Backend entry point
 │  ├─ install_angela.py          # One-click installer
 │  └─ setup.py                   # Local installation script
 │
 ├─ 🎮 Desktop App (apps/desktop-app/)
 │  ├─ electron_app/              # Electron application
 │  │  ├─ main.js                # Main process
 │  │  ├─ preload.js             # IPC bridge
 │  │  ├─ index.html             # Main UI
 │  │  ├─ settings.html          # Settings page
 │  │  ├─ package.json           # Dependencies
 │  │  ├─ assets/               # Resources (icon, etc.)
 │  │  └─ js/                   # JavaScript modules (52 files)
 │  │     ├─ app.js              # Application coordinator
 │  │     ├─ live2d-manager.js    # Live2D integration
 │  │     ├─ live2d-cubism-wrapper.js  # Live2D SDK wrapper
 │  │     ├─ live2d-test.js      # Test suite
 │  │     ├─ audio-handler.js     # Audio I/O
 │  │     ├─ backend-websocket.js # Backend connection
 │  │     ├─ state-matrix.js     # 8D state sync
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
 │  │     ├─ settings.js        # Settings management
 │  │     └─ security-manager.js # A/B/C security logic
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
  │  ├─ main.py                    # App A: System management server (9 routes)
  │  └─ src/                       # Source code
  │     ├─ services/               # App B: Main AI server (~104 routes)
  │     │  ├─ main_api_server.py   # Server entry point
  │     │  ├─ api/                 # State Matrix API (34 routes)
  │     │  └─ ...                  # Chat, LLM, Atlassian services
  │     ├─ api/                    # Shared router
  │     │  ├─ router.py            # /api/v1/* routes (used by both servers)
  │     │  └─ v1/endpoints/        # drive, pet endpoints
  │     ├─ core/                   # Core components
  │     │  ├─ autonomous/          # Biological systems (47 files)
  │     │  ├─ metamorphosis/       # Identity/creation
  │     │  ├─ precision/           # Precision management
  │     │  ├─ system/              # Phase 6+7 self-evolution
  │     │  │  ├─ bootstrap/        #   Init + state persistence
  │     │  │  ├─ config/           #   Tiered config loader
  │     │  │  ├─ evolution/        #   ConfigMutator
  │     │  │  └─ state_store/      #   Cross-component broadcast
  │     │  └─ knowledge/           # Knowledge/memory
  │     ├─ ai/                     # Level 5 ASI Core (46 subdirs)
  │     │  ├─ alignment/           # Reasoning, Emotion System
  │     │  ├─ lis/                 # Linguistic Immune System
  │     │  ├─ integration/         # Unified Control Center (UCC)
  │     │  ├─ memory/              # HAM, LU memory systems
  │     │  ├─ learning/            # Learning manager, content analyzer
  │     │  ├─ response/            # NeuroAutoSelector, NGR
  │     │  └─ ...                  # 40+ additional AI modules
  │     ├─ config/                 # YAML configuration
  │     ├─ shared/                 # Middleware, security, utils
  │     ├─ economy/                # Economy manager, gacha
  │     ├─ pet/                    # Pet lifecycle, biological integrator
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
     ├─ unit/                     # Unit tests
     └─ ...                       # ~237 test_*.py files total
```

---

## 🛠️ Configuration / 配置說明

### Settings Page Categories / 設置分類

1. **General**: Basic settings (name, language, theme)
   / 基本設定（名稱、語言、主題）
2. **Appearance**: Live2D model, scale, position / 外觀設定（模型、縮放、位置）
3. **Behavior**: Autonomy, curiosity, social drive
   / 行為邏輯（自主性、好奇心、社交驅動）
4. **Performance**: Performance mode, FPS target / 性能調優（模式、FPS 目標）
5. **Audio**: TTS engine, voice, microphone / 音訊交互（TTS、語音、麥克風）
6. **Desktop**: File operations, wallpaper / 桌面整合（文件操作、桌布）
7. **Advanced**: Debug options, log level / 進階設定（除錯、日誌等級）
8. **About**: Version info, credits / 關於（版本資訊、貢獻）

### Backend Configuration / 後端配置

The backend has two config systems during the ongoing migration:

**Legacy (stable):**
- `apps/backend/src/config/angela_core.yaml` — primary AI config (27 sections, 12 marked dead)
- `apps/backend/configs/` — flat YAML files (config.yaml, performance_config.yaml, etc.)
- Desktop settings stored in `localStorage`.

**New 3-Tier System (Phase 7, incremental migration):**
- **S-Level** (`configs/system/`): Core infrastructure, bootstrap, keys — low evolution权限
- **A-Level** (`configs/standard/`): Runtime parameters (science, behavior, matrix) — high evolution权限
- **M-Level** (`configs/mods/`): User mods and plugins — medium evolution权限
- **Override chain**: `*.default.yaml` ← `*.user.yaml` ← `*.evolved.yaml`
- See [CONFIG_ARCHITECTURE.md](CONFIG_ARCHITECTURE.md) for full spec.

---

## 🧪 Live2D Model / 模型資訊

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

## 🧪 Testing / 測試

### Live2D Test Suite

Run automated tests in browser console:

```javascript
const testSuite = new Live2DTestSuite()
const canvas = document.getElementById('live2d-canvas')
await testSuite.initialize(canvas)
await testSuite.runAllTests()
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

See [CROSS_PLATFORM_TESTING.md](docs/CROSS_PLATFORM_TESTING.md) for
comprehensive testing procedures.

---

## 📊 Performance Metrics

| Metric               | Value            | Target    |
| -------------------- | ---------------- | --------- |
| Live2D FPS           | 60 (target)      | 60        |
| Memory Usage         | < 100MB          | 100MB     |
| CPU Usage            | < 5%             | 5%        |
| Audio Latency        | < 50ms           | 50ms      |
| **Security Latency** | **< 2ms (HMAC)** | **5ms**   |
| **ABC Key Sync**     | **< 50ms**       | **100ms** |
| Python Source Lines  | 116,265         | (84% live, 9% dead, 7% semi-finished) |
| Desktop App JS Files | 63              | (52 JS modules)                         |
| Python Source Files  | 515             | -                                       |
| Test Files (tests/)  | 327             | -                                       |
| AI Agents            | 15              | -                                       |
| Autonomous Modules   | 49              | -                                       |
| Mobile App Modules   | 5               | -                                       |
| Native Audio Modules | 3               | -                                       |

> For more detailed system indicators, cluster performance, and precision
> mapping, please refer to [metrics.md](metrics.md).

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

Special thanks to the following projects and communities:

- **Live2D Cubism SDK**: For the amazing 2D animation technology.
- **FastAPI**: For the high-performance backend framework.
- **Electron**: For the cross-platform desktop application framework.
- **Google Gemini & OpenAI**: For providing the core cognitive capabilities.
- **Miara Pro Model**: The beautiful Live2D character model.
- **And all other open-source dependency library developers.**

---

  **Last Updated**: 2026-05-21 **Version**: 6.5.0-dev (Self-Evolution)

### Current Status (v6.5.0-dev — Self-Evolution Phase 6+7)

**Active development** on Self-Evolution (Phase 6) and Tiered Config Architecture (Phase 7). Previous phases (1-5, Post-Refactor, NGR v6.4) complete.

#### Phase 6 — Self-Evolution Loop ✅

| Component | File | Status |
|-----------|------|--------|
| ConfigMutator (validation + atomic write) | `core/system/evolution/config_mutator.py` | ✅ Done |
| LLM config hot-reload | `services/angela_llm_service.py` | ✅ Done |
| Evolution chat confirmation | `services/chat_service.py` | ✅ Done |
| Bootstrap broadcast | `core/system/bootstrap/bootstrap_manager.py` | ✅ Done |
| StateStore | `core/system/state_store/` | ✅ Done |

#### Phase 7 — Tiered Config Architecture (TCS) 🟡

| Component | Path | Status |
|-----------|------|--------|
| TieredConfigLoader (Default→User→Angela) | `core/system/config/tiered_loader.py` | ✅ Done |
| S-level: bootstrap, core, keys | `configs/system/*.default.yaml` | ✅ Defaults exist |
| A-level: science params | `configs/standard/science/*.default.yaml` | ✅ Defaults exist |
| A-level: behavior params | `configs/standard/behavior/dynamic.default.yaml` | ✅ Defaults exist |
| A-level: matrix | `configs/standard/matrix/` | ⚠️ Empty dir |
| A-level: text assets | `configs/standard/text/` | ❌ Missing |
| M-level: mods | `configs/mods/` | ⚠️ Empty dir |
| `.user.yaml` overlays | All tiers | ⏳ Not Started |
| `.evolved.yaml` overlays | All tiers | ⏳ Not Started |
| ConfigMutator → `*.evolved.yaml` | `config_mutator.py` | 🟡 Being rewritten |
| `config_loader.py` redirect | `config_loader.py` | 🟡 Partial |
| Legacy flat configs → tiered | 23 files in `configs/` root | 🟡 Migration started |

#### Hardcoded Thresholds Still in Code (`apps/backend/src/`)

23+ values across 8+ files — all candidates for config externalization:

| Pattern | Files | Example |
|---------|-------|---------|
| `arousal > N` / `arousal < N` | 8 files, 19 occ | `heartbeat.py:135` (`0.7`), `biological_integrator.py:294` (`70`), `autonomic_nervous_system.py:351` (`0.6`) |
| `random.random() < N` | 5 files, 8 occ | `heartbeat.py:135` (`0.1`), `agent_monitoring_manager.py:136` (`0.95`) |
| `target_fps = N` | 3 files, 6 occ | `visual_config.py:316` (`30`), `visual_config.py:325` (`60`), `visual_config.py:398` (`144`) |

#### Config Sprawl (5+ Locations)

| Location | Files | Role |
|----------|-------|------|
| `apps/backend/configs/` | 23 files | Main runtime configs (legacy flat + new tiered) |
| `apps/backend/src/config/` | 6 files | Source-level configs (angela_core.yaml, llm_providers.yaml, etc.) |
| `config/` (project root) | 5 files | Project-level config (mcp.json, angela_config.yaml) |
| `configs/` (project root) | 5 files | Additional global configs (pytest, pyright) |

#### Previous: v6.4.0 — [auto] LLM Mode (NeuroAutoSelector)

Angela can automatically select LLM backend, model, and parameters based on hardware detection, system load, task analysis, and 8D state correction. Files: `ai/response/neuro_auto_selector.py`.

### Roadmap

| Priority | Task | Status | Description |
|----------|------|--------|-------------|
| **P8** 🔴 | Tech Debt Cleanup | 🆕 Planned | 6-week prioritized cleanup: god modules, security, singleton, dead code, logging, DI. See [PHASE_8_PLAN](docs/plans/PHASE_8_DEBT_CLEANUP.md) |
| **P7** 🟡 | TCS Config Migration | 🟡 Progress | Complete 3-tier adoption, purge 23+ hardcoded values, create user/evolved overlays |
| **P6.5** 🟢 | Startup Wiring | ✅ Done | `MetabolicHeartbeat.start()` + `_initialize_all_services()` wired into `main_api_server.py` lifespan |
| **P8.5** 🔴 | True LLM End-to-End | ⏳ Pending | MathVerifier → CodeInspector → StateMatrixAdapter real flow (after P8 cleanup) |
| **P9** 🟡 | Persistence Layer | ⏳ Pending | save_state/load_state → Redis/JSON |

For full architecture details, see [ANGELA_STATUS.md](ANGELA_STATUS.md), [CONFIG_ARCHITECTURE.md](CONFIG_ARCHITECTURE.md), [WIRING_MAP](docs/analysis/WIRING_MAP_2026-05-21.md) (server lifecycle, factory chains, subtle wiring, dead code), [CODE_STATISTICS](docs/analysis/CODE_STATISTICS_2026-05-21.md) (live vs dead code breakdown, semi-finished systems), [MODULARITY_ANALYSIS](docs/analysis/MODULARITY_ANALYSIS_2026-05-21.md) (coupling, god modules, singleton abuse), [PROBLEM_ANALYSIS](docs/analysis/PROBLEM_ANALYSIS_2026-05-21.md) (architect/AI-researcher/engineering perspectives), and [PHASE_8_PLAN](docs/plans/PHASE_8_DEBT_CLEANUP.md) (6-week prioritized cleanup roadmap).

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
  <i>Active Development 🔄 — Phase 6+7 Self-Evolution</i>
</p>

<p align="center">
  🌟✨🖥️🎭🎵💻🌐
</p>

---

**Version**: 6.5.0-dev
**Release Date**: 2026-05-21
**Status**: Active Development 🔄 | Phase 6+7 Self-Evolution | NGR v6.4
**Platforms**: Windows, macOS, Linux (Mobile Bridge: stub only)
**Code Stats**: 500+ Python Source Files, ~114,000 Lines, 63 Desktop JS Modules
**Test Status**: ~237 test_*.py files in tests/
