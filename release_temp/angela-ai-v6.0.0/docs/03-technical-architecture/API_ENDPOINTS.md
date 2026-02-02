# API Endpoints

This document provides detailed information about the backend API endpoints for the Unified AI Project.

## Base URL

All API endpoints are relative to the base URL:
```
http://localhost:8000/api
```

In production, this would be replaced with the actual domain.

## Authentication

Most endpoints require authentication. Authentication is handled through API keys passed in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

## Health Check

### GET /health

Check the health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Agent Management

### GET /agents

Retrieve a list of all available AI agents.

**Response:**
```json
{
  "agents": [
    {
      "id": "creative-writing-agent",
      "name": "Creative Writing Agent",
      "description": "Specialized in creative writing and content generation"
    },
    {
      "id": "image-generation-agent",
      "name": "Image Generation Agent",
      "description": "Generates images based on text descriptions"
    },
    {
      "id": "web-search-agent",
      "name": "Web Search Agent",
      "description": "Performs web searches and retrieves information"
    }
  ]
}
```

### POST /agents/{agent_id}/task

Submit a task to a specific agent.

**Request Body:**
```json
{
  "task": "Write a short story about a robot learning to paint",
  "parameters": {
    "style": "sci-fi",
    "length": "short"
  }
}
```

**Response:**
```json
{
  "task_id": "task_12345",
  "status": "submitted",
  "message": "Task submitted successfully"
}
```

### GET /agents/{agent_id}/task/{task_id}

Check the status of a specific task.

**Response:**
```json
{
  "task_id": "task_12345",
  "status": "completed",
  "result": "Once upon a time, in a world of circuits and steel...",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Memory Management

### POST /memory/store

Store information in the HAM memory system.

**Request Body:**
```json
{
  "content": "The sky is blue because of Rayleigh scattering",
  "tags": ["science", "physics", "optics"],
  "metadata": {
    "source": "user_input",
    "confidence": 0.95
  }
}
```

**Response:**
```json
{
  "memory_id": "mem_12345",
  "status": "stored",
  "message": "Information stored successfully"
}
```

### GET /memory/retrieve

Retrieve information from the HAM memory system.

**Query Parameters:**
- `query`: The search query
- `limit`: Maximum number of results (default: 10)

**Response:**
```json
{
  "results": [
    {
      "memory_id": "mem_12345",
      "content": "The sky is blue because of Rayleigh scattering",
      "relevance": 0.95,
      "tags": ["science", "physics", "optics"],
      "timestamp": "2023-01-01T00:00:00Z"
    }
  ]
}
```

## Training Management

### POST /training/start

Start a training session.

**Request Body:**
```json
{
  "model_type": "concept_model",
  "training_data": "path/to/training/data",
  "parameters": {
    "epochs": 100,
    "batch_size": 32,
    "learning_rate": 0.001
  }
}
```

**Response:**
```json
{
  "training_id": "train_12345",
  "status": "started",
  "message": "Training session started successfully"
}
```

### GET /training/status/{training_id}

Check the status of a training session.

**Response:**
```json
{
  "training_id": "train_12345",
  "status": "running",
  "progress": 0.75,
  "epoch": 75,
  "total_epochs": 100,
  "metrics": {
    "loss": 0.05,
    "accuracy": 0.92
  }
}
```

## HSP Protocol

### POST /hsp/register

Register a new service with the HSP protocol.

**Request Body:**
```json
{
  "service_id": "my-service",
  "capabilities": ["text_generation", "image_processing"],
  "endpoint": "http://my-service:8080/hsp"
}
```

**Response:**
```json
{
  "service_id": "my-service",
  "status": "registered",
  "message": "Service registered successfully"
}
```

### POST /hsp/message

Send a message through the HSP protocol.

**Request Body:**
```json
{
  "sender": "unified-ai",
  "recipient": "my-service",
  "message_type": "REQUEST",
  "content": "Generate a description of a sunset"
}
```

**Response:**
```json
{
  "message_id": "msg_12345",
  "status": "sent",
  "message": "Message sent successfully"
}
```

## System Monitoring

### GET /monitoring/metrics

Retrieve system performance metrics.

**Response:**
```json
{
  "timestamp": "2023-01-01T00:00:00Z",
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 34.1,
  "network_io": {
    "bytes_sent": 1024000,
    "bytes_received": 2048000
  }
}
```

### GET /monitoring/logs

Retrieve recent system logs.

**Query Parameters:**
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `limit`: Maximum number of logs to retrieve (default: 50)

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2023-01-01T00:00:00Z",
      "level": "INFO",
      "message": "Agent task completed successfully",
      "component": "AgentManager"
    }
  ]
}
```

## Error Handling

All API endpoints follow standard HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **404**: Not Found
- **500**: Internal Server Error

Error responses follow this format:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": "Additional details about the error"
}
```

## Rate Limiting

To ensure fair usage and system stability, API requests may be rate-limited:

- **Anonymous requests**: 100 requests per hour
- **Authenticated requests**: 1000 requests per hour

Exceeding rate limits will result in a 429 (Too Many Requests) response.

## Versioning

The API follows semantic versioning. Breaking changes will be introduced in new major versions, while backward-compatible changes will be added in minor versions.

Current API version: v1

## Changelog

### v1.0.0
- Initial release of the API
- Basic agent management endpoints
- Memory storage and retrieval
- Training management
- HSP protocol integration
- System monitoring

### v1.1.0
- Added rate limiting
- Improved error handling
- Enhanced documentation
- Added health check endpoint

## Support

For API support and questions, please:

1. Check the documentation
2. Review existing issues on GitHub
3. Create a new issue if your question is not addressed