# CLI Usage Guide

This guide provides detailed instructions for using the command-line interface (CLI) tools included in the Unified AI Project.

## Overview

The Unified AI Project includes several CLI tools designed to interact with different aspects of the system:

1. **Unified CLI** - General AI interaction and system management
2. **AI Models CLI** - Model management and interaction
3. **HSP CLI** - Heterogeneous Service Protocol tools
4. **Training CLI** - Model training and evaluation tools

## Installation

### Option 1: Using the Unified Management Tool

1. Double-click `unified-ai.bat`
2. Select "CLI Tools"
3. Choose "Install CLI Tools"
4. Follow the on-screen instructions

### Option 2: Manual Installation

1. Navigate to the tools directory:
   ```bash
   cd tools/
   ```

2. Install the CLI tools:
   ```bash
   ./cli-runner.bat install
   ```

## Unified CLI

The Unified CLI provides general interaction with the AI system.

### Basic Commands

#### Health Check
Check the health status of the system:
```bash
unified-cli health
```

#### Chat with AI
Have a conversation with the AI:
```bash
unified-cli chat "Hello, how are you today?"
```

#### System Information
Get information about the system:
```bash
unified-cli info
```

### Advanced Commands

#### Agent Management
List available agents:
```bash
unified-cli agents list
```

Get details about a specific agent:
```bash
unified-cli agents info creative-writing-agent
```

#### Memory Operations
Store information in memory:
```bash
unified-cli memory store "The sky is blue" --tags science,physics
```

Retrieve information from memory:
```bash
unified-cli memory retrieve "Why is the sky blue?"
```

#### Task Management
Submit a task to an agent:
```bash
unified-cli task submit creative-writing-agent "Write a poem about autumn"
```

Check task status:
```bash
unified-cli task status task_12345
```

## AI Models CLI

The AI Models CLI provides tools for managing and interacting with AI models.

### Model Management

#### List Models
List all available models:
```bash
ai-models-cli list
```

#### Model Information
Get detailed information about a specific model:
```bash
ai-models-cli info concept-model-environment-simulator
```

#### Model Status
Check the status of a model:
```bash
ai-models-cli status concept-model-environment-simulator
```

### Model Interaction

#### Generate Content
Generate content using a specific model:
```bash
ai-models-cli generate creative-writing-agent "Write a short story about a robot"
```

#### Evaluate Model
Evaluate model performance:
```bash
ai-models-cli evaluate concept-model-causal-reasoning --test-data path/to/test/data
```

## HSP CLI

The HSP CLI provides tools for working with the Heterogeneous Service Protocol.

### Service Management

#### Register Service
Register a new service with the HSP network:
```bash
hsp-cli register --service-id my-service --endpoint http://localhost:8080/hsp
```

#### List Services
List all registered services:
```bash
hsp-cli services list
```

#### Service Information
Get information about a specific service:
```bash
hsp-cli services info my-service
```

### Message Handling

#### Send Message
Send a message through the HSP protocol:
```bash
hsp-cli message send --recipient my-service --content "Hello, service!"
```

#### Receive Messages
Listen for incoming messages:
```bash
hsp-cli message listen
```

## Training CLI

The Training CLI provides tools for model training and evaluation.

### Training Management

#### Start Training
Start a training session:
```bash
training-cli start --model concept-model-adaptive-learning --data path/to/training/data
```

#### Training Status
Check the status of a training session:
```bash
training-cli status training_12345
```

#### Stop Training
Stop a training session:
```bash
training-cli stop training_12345
```

### Model Evaluation

#### Evaluate Model
Evaluate a trained model:
```bash
training-cli evaluate --model concept-model-adaptive-learning --test-data path/to/test/data
```

#### Compare Models
Compare the performance of different models:
```bash
training-cli compare model_1 model_2 model_3
```

## Configuration

### Environment Variables

The CLI tools can be configured using environment variables:

- `UNIFIED_AI_API_KEY`: API key for authentication
- `UNIFIED_AI_API_ENDPOINT`: API endpoint URL
- `UNIFIED_AI_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Configuration Files

CLI tools can also be configured using YAML files located in `~/.unified-ai/config.yaml`:

```yaml
api:
  endpoint: "http://localhost:8000"
  key: "your-api-key"

logging:
  level: "INFO"
  file: "~/.unified-ai/logs/cli.log"

models:
  default: "concept-model-environment-simulator"
```

## Advanced Usage

### Scripting

The CLI tools can be used in scripts for automation:

```bash
#!/bin/bash

# Check system health
unified-cli health

# If healthy, start training
if [ $? -eq 0 ]; then
  training-cli start --model concept-model-adaptive-learning --data ./training-data/
fi
```

### Batch Operations

Perform batch operations on multiple items:

```bash
# Train multiple models
for model in model1 model2 model3; do
  training-cli start --model $model --data ./training-data/
done
```

### Custom Commands

Create custom commands by extending the CLI tools:

1. Create a new Python script
2. Import the CLI modules
3. Add custom functionality
4. Register the new commands

## Troubleshooting

### Common Issues

#### Command Not Found
If you get a "command not found" error:
1. Ensure the CLI tools are installed
2. Check that the tools directory is in your PATH
3. Try using the full path to the CLI runner

#### Authentication Errors
If you encounter authentication errors:
1. Verify your API key is correct
2. Check that the API endpoint is accessible
3. Ensure your environment variables are set correctly

#### Network Issues
If you experience network issues:
1. Check your internet connection
2. Verify the API endpoint URL
3. Check firewall settings

### Debugging

Enable debug logging for detailed information:
```bash
export UNIFIED_AI_LOG_LEVEL=DEBUG
unified-cli health
```

### Getting Help

Each CLI tool includes built-in help:

```bash
unified-cli --help
unified-cli chat --help
ai-models-cli --help
hsp-cli --help
training-cli --help
```

## Best Practices

### Security

1. Never commit API keys to version control
2. Use environment variables for sensitive information
3. Regularly rotate API keys
4. Use secure connections (HTTPS) when possible

### Performance

1. Use appropriate batch sizes for operations
2. Monitor resource usage during long-running operations
3. Implement proper error handling and retry logic
4. Use caching for frequently accessed data

### Automation

1. Use scripts for repetitive tasks
2. Implement proper logging for automated processes
3. Handle errors gracefully in automated workflows
4. Monitor automated processes for issues

## Examples

### Daily Workflow

A typical daily workflow might include:

```bash
# Check system health
unified-cli health

# Chat with AI for daily planning
unified-cli chat "What should I focus on today?"

# Check training progress
training-cli status latest

# Evaluate model performance
training-cli evaluate --model current-model --test-data ./daily-tests/
```

### Model Development

A model development workflow:

```bash
# Start with a health check
unified-cli health

# List available models
ai-models-cli list

# Start training a new model
training-cli start --model new-concept-model --data ./training-data/ --epochs 100

# Monitor training progress
while true; do
  training-cli status latest
  sleep 60
done

# Evaluate the trained model
training-cli evaluate --model new-concept-model --test-data ./test-data/
```

### System Administration

System administration tasks:

```bash
# Check overall system health
unified-cli health

# List all agents and their status
unified-cli agents list

# Check memory usage
unified-cli memory stats

# List all services
hsp-cli services list

# Check training jobs
training-cli jobs list
```

## Conclusion

The CLI tools provide powerful command-line access to the Unified AI Project's functionality. By following this guide, you can effectively use these tools for development, testing, and system administration tasks. Remember to consult the built-in help for detailed information about specific commands and options.