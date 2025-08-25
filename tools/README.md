# Tools Directory

This directory contains various utility scripts and tools for the Unified AI Project.

## Available Tools

### Development Tools
- [start-dev.bat](start-dev.bat) - Start development environment
- [health-check.bat](health-check.bat) - Check development environment health
- [run-tests.bat](run-tests.bat) - Run test suite
- [cli-runner.bat](cli-runner.bat) - Run CLI tools

### Git Management Tools
- [safe-git-cleanup.bat](safe-git-cleanup.bat) - Clean Git status safely
- [emergency-git-fix.bat](emergency-git-fix.bat) - Recover from Git issues
- [fix-git-10k.bat](fix-git-10k.bat) - Fix Git issues with 10K limit

### Training Tools
- [setup-training.bat](setup-training.bat) - Prepare for AI training
- [train-manager.bat](train-manager.bat) - Manage training data and processes

## 📋 Important Note

As part of our project structure optimization, all batch scripts have been moved to this `tools/` directory. 
The root directory now only contains two essential scripts:
- `unified-ai.bat` - Unified management tool for human users
- `ai-runner.bat` - Automated tool for AI agents

To use any of the tools listed above, you can either:
1. Run them directly with their full path: `tools\script-name.bat`
2. Use the unified management tool: `unified-ai.bat` (recommended)

## CLI Tools

The Unified AI Project provides several CLI tools for interacting with the system:

### Unified CLI
General AI interactions with the backend services:
```bash
# Check system health
cli-runner.bat unified-cli health

# Chat with AI
cli-runner.bat unified-cli chat "Hello, how are you?"

# Analyze code
cli-runner.bat unified-cli analyze --code "def hello(): print('Hello')"
```

### AI Models CLI
Model management and interactions with various AI models:
```bash
# List available models
cli-runner.bat ai-models-cli list

# Check model health
cli-runner.bat ai-models-cli health

# Query AI models
cli-runner.bat ai-models-cli query "Explain quantum computing"

# Enter chat mode
cli-runner.bat ai-models-cli chat --model gpt-4
```

### HSP CLI
Hyper-Structure Protocol tools for advanced interactions:
```bash
# Query using HSP
cli-runner.bat hsp-cli query "Hello"

# Publish facts via HSP
cli-runner.bat hsp-cli publish_fact "The sky is blue" --confidence 0.9
```

### Installing CLI as System Command
You can install the CLI tools as system commands:
```bash
# Install CLI package
cli-runner.bat install-cli
```

After installation, you can use the `unified-ai` command from anywhere:
```bash
unified-ai --help
unified-ai health
unified-ai chat "Hello"
```