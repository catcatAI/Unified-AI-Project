# Angela AI - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Clone and Install
```bash
git clone https://github.com/your-repo/Unified-AI-Project.git
cd Unified-AI-Project

# Install Python dependencies
pip install -r requirements.txt

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
Create `.env` file in project root:
```
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Option C: GUI Key Manager**
```bash
python apps/backend/src/core/desktop/key_manager_gui.py
```

### Step 3: Start Angela

```bash
# Auto-detect hardware and select mode
python -m apps.backend.src.main

# Or specify mode explicitly
python -m apps.backend.src.main --mode=standard
```

## 📊 Choose Your Mode

Angela automatically selects the best mode based on your hardware:

### 🟢 Lite Mode (64 dimensions)
**For**: Raspberry Pi, old laptops, mobile devices
- **Hardware**: 4GB RAM, no GPU
- **LLM**: Local only (Ollama/llama.cpp with TinyLlama 1.1B)
- **Features**: Basic conversation, simple emotions
- **Memory**: 100 memories, daily consolidation
- **Quality**: Basic AI companion

```bash
python -m apps.backend.src.main --mode=lite
```

### 🔵 Standard Mode (384 dimensions)
**For**: Modern laptops and desktops
- **Hardware**: 8GB RAM, GPU optional
- **LLM**: OpenAI GPT-3.5/Claude 3 Haiku + local fallback
- **Features**: Learning, 5-second prediction, coherent personality
- **Memory**: 10K memories, hourly consolidation
- **Quality**: Good AI companion with personality

```bash
python -m apps.backend.src.main --mode=standard
```

### 🟣 Extended Mode (4096 dimensions)
**For**: Gaming PCs, workstations
- **Hardware**: 16GB+ RAM, GPU with 8GB+ VRAM
- **LLM**: GPT-4/Claude 3 Opus + multi-model ensemble voting
- **Features**: Full learning, 60-second multi-world prediction, dreaming, self-modification
- **Memory**: 1M memories, continuous consolidation
- **Quality**: Advanced AI companion with creativity and reflection

```bash
python -m apps.backend.src.main --mode=extended
```

## 🖥️ System Tray Features

Right-click Angela icon in system tray to:

- **Switch Mode**: Change between Lite/Standard/Extended on-the-fly
- **API Keys**: Open key manager GUI
- **Settings**: Configure preferences
- **Status**: View current memory count, mode, uptime
- **Exit**: Shutdown Angela

## ⚙️ Configuration Files

### Main Config: `apps/backend/configs/config.yaml`

Three mode templates are pre-configured. Edit to customize:

```yaml
angela_modes:
  standard:
    llm:
      primary_backend: "openai"
      model: "gpt-4"  # Change to your preferred model
      temperature: 0.7
    
    memory:
      max_capacity: 10000
      consolidation: "hourly"
    
    features:
      learning: true
      prediction:
        enabled: true
        horizon: 5  # Prediction window in seconds
```

### Local Model Config: `apps/backend/configs/multi_llm_config.json`

Configure Ollama and llama.cpp:

```json
{
  "models": {
    "tinyllama-local": {
      "provider": "ollama",
      "backend_type": "ollama",
      "base_url": "http://localhost:11434",
      "model_name": "tinyllama"
    },
    "llamacpp-local": {
      "provider": "llamacpp", 
      "backend_type": "llamacpp",
      "base_url": "http://localhost:8080",
      "model_name": "llama-3-8b"
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

- **Customize personality**: Edit `config.yaml` -> `angela_modes` -> `homeostatic_targets`
- **Add more memories**: Increase `max_capacity` in config
- **Enable dreaming**: Set `dreaming: true` in Extended mode
- **Read full docs**: See `docs/` directory for detailed architecture

## 🤝 Support

- Issues: https://github.com/your-repo/Unified-AI-Project/issues
- Discussions: https://github.com/your-repo/Unified-AI-Project/discussions

---

**Privacy Note**: Angela AI respects your privacy. With local models (Ollama/llama.cpp), all processing happens on your device. No data is sent to external servers.
