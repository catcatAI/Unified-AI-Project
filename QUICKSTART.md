# Angela AI v7.5.0-dev - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Clone and Install
```bash
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# (Recommended) Setup and activate Python virtual environment (.venv)
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install Python backend dependencies
pip install -r apps/backend/requirements.txt

# Install JS workspace dependencies (use npx if pnpm is not installed globally)
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all

# For local models, install Ollama
# Windows: https://ollama.com/download/windows
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Configure API Keys

**Option A: Environment Variables (Recommended - Most Secure)**
```bash
# Linux/macOS
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-key-here
```

**Option B: .env File**
Edit `.env` file in project root:
```
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Start Angela

#### 方式一：统一启动脚本（推荐）
```bash
# Windows:
python scripts/run_angela.py              # 启动全部
python scripts/run_angela.py --api-only   # 只启动后端
python scripts/run_angela.py --health-check  # 健康检查

# Linux/Mac:
python scripts/run_angela.py              # 启动全部
python scripts/run_angela.py --api-only   # 只启动后端
python scripts/run_angela.py --health-check  # 健康检查
```

#### 方式二：手动启动后端
```bash
cd apps/backend
python3 -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
```

#### 方式三：Python 脚本
```bash
python scripts/run_angela.py              # 启动全部
python scripts/run_angela.py --api-only   # 只启动后端
python scripts/run_angela.py --health-check  # 健康检查
```

## 🤖 LLM Configuration

Angela AI uses a pluggable LLM architecture. Configure providers in:
- **Environment variables**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- **Config file**: `apps/backend/configs/multi_llm_config.json`

Available backends: OpenAI, Anthropic, Google Gemini, Ollama (local), llama.cpp (local), ED3N, GARDEN.

## 🖥️ System Tray Features

Right-click Angela icon in system tray to:

- **Start/Stop Backend**: Launch or shutdown the backend service
- **Start Desktop App**: Launch the Electron desktop application
- **Settings**: Configure preferences (General, Appearance, Behavior, Performance, Audio, Desktop, Advanced)
- **Status**: View current memory count, mode, uptime
- **About**: Version information and credits
- **Exit**: Shutdown Angela

## ⚙️ Configuration Files

### Main Config: `apps/backend/configs/system_config.yaml`

System configuration including crisis management, emotional parameters, timeout settings, and monitoring.

### LLM Config: `apps/backend/configs/multi_llm_config.json`

Multi-backend LLM configuration supporting Ollama, OpenAI, and Anthropic:

```json
{
  "models": {
    "ollama-local": {
      "provider": "ollama",
      "backend_type": "ollama",
      "base_url": "http://localhost:11434",
      "model_name": "llama3.2:1b",
      "enabled": true
    },
    "openai-gpt4": {
      "provider": "openai",
      "backend_type": "openai",
      "base_url": "https://api.openai.com/v1",
      "model_name": "gpt-4",
      "enabled": false
    }
  }
}
```

## 🔐 Security Best Practices

1. **Never commit API keys** - `.env` and config files with keys are in `.gitignore`
2. **Use environment variables** - Most secure option, keys not stored in files
3. **Local models are private** - No data leaves your device with Ollama/llama.cpp
4. **Key Manager GUI** - Shows only "configured" status, never displays key values

## 🛠️ Hardware Detection

Angela auto-detects on startup:

```python
from apps.backend.src.core.system.hardware_detector import HardwareDetector, ModeRecommender

# Detect hardware
detector = HardwareDetector()
profile = detector.detect()
print(f"RAM: {profile.ram_gb:.1f}GB, GPU: {profile.gpu_name or 'None'}")

# Recommend mode
recommender = ModeRecommender(config)
mode, reason, mode_config = recommender.recommend_mode()
print(f"Recommended: {mode} - {reason}")
```

## 📱 Model Provider Setup

### OpenAI
```bash
export OPENAI_API_KEY="sk-..."
```
Models: gpt-3.5-turbo, gpt-4, gpt-4o

### Anthropic Claude
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Models: claude-3-haiku, claude-3-sonnet, claude-3-opus

### Google Gemini
```bash
export GEMINI_API_KEY="..."
```
Models: gemini-1.5-flash, gemini-1.5-pro

### Local Models (Ollama)
```bash
# Install Ollama and pull model
ollama pull tinyllama
ollama pull llama3

# Start server (default: localhost:11434)
ollama serve
```
No API key needed for local models!

### Local Models (llama.cpp)
```bash
# Build llama.cpp with server
make llama-server

# Start server (OpenAI-compatible API)
./llama-server -m models/llama-3-8b.gguf --port 8080
```

## 🚨 Troubleshooting

### "No API key configured"
- Set environment variable or use GUI key manager
- Check that key is valid and has credits

### "Out of memory" 
- Angela will auto-downgrade mode if enabled
- Or manually switch to Lite mode

### "Local model not responding"
- Check Ollama/llama.cpp server is running
- Verify base_url in config matches server address
- Test: `curl http://localhost:11434/api/tags` (Ollama)

### Slow responses
- Lite mode: ~500ms-2s (local CPU)
- Standard mode: ~200ms-1s (API)
- Extended mode: ~100ms-500ms (API + local ensemble)

## 📚 Next Steps

- **Customize personality**: Edit `apps/backend/configs/system_config.yaml`
- **Add more memories**: Increase memory capacity in configuration
- **Read full docs**: See `docs/` directory for detailed architecture
- **View Live2D models**: Check `apps/desktop-app/electron_app/models/` directory
- **Test Angela**: Run `python3 -m pytest tests/` for comprehensive testing

## 🤝 Support

- **GitHub**: https://github.com/catcatAI/Unified-AI-Project
- **Issues**: https://github.com/catcatAI/Unified-AI-Project/issues
- **Documentation**: See `docs/` directory for detailed guides

## 📊 Project Stats

- **Version**: 7.5.0-dev
- **Python Files**: 612 (backend src ~96K lines)
- **JavaScript Modules**: 50+ shared across 3 apps
- **Tests**: ~4,387 tests collected (tests/), 0 collection errors
- **Status**: Active Development 🚧 — see [README.md](README.md) for details

---

**Privacy Note**: Angela AI respects your privacy. With local models (Ollama), all processing happens on your device. No data is sent to external servers unless you explicitly configure external APIs.
