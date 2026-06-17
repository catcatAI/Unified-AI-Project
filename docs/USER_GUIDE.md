# Angela AI - User Guide

## Introduction

Angela AI is an advanced AI assistant with memory, learning, and emotional intelligence capabilities. This guide will help you get started with Angela.

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for web dashboard)
- Docker (optional, for containerized deployment)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/unified-ai-project.git
cd unified-ai-project

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for web dashboard)
cd apps/web-dashboard
npm install
cd ../..
```

## Starting Angela

### Backend Server

```bash
# Start the backend server
cd apps/backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Web Dashboard

```bash
# Start the web dashboard
cd apps/web-dashboard
npm run dev
```

### Docker Deployment

```bash
# Start all services with Docker Compose
docker-compose up -d
```

## Using Angela

### Chat Interface

1. Open the web dashboard at `http://localhost:3000`
2. Navigate to the Chat panel
3. Type your message and press Enter or click Send
4. Angela will respond with intelligent, contextual replies

### Voice Interaction

Angela supports voice input and output:
- Click the microphone icon to speak
- Angela will respond with voice when available

### Pet Interaction

The pet panel shows Angela's virtual companion:
- **Pet**: Increase happiness
- **Feed**: Reduce hunger
- **Play**: Increase energy
- **Rest**: Restore energy

## Features

### Memory System

Angela remembers your conversations and preferences:
- View memories in the Memory Viewer
- Search and filter by category
- Memories improve over time

### Learning

Angela learns from every interaction:
- ED3N dictionary grows with new terms
- GARDEN reasoning improves with use
- Learning Dashboard shows progress

### Safety

Angela has a 3-layer safety system:
1. **Trust Manager**: Tracks user trust scores
2. **Content Filter**: Blocks harmful content
3. **Safety Audit**: Logs all safety decisions

## API Usage

### REST API

```bash
# Chat with Angela
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Angela!"}'

# Get system status
curl http://localhost:8000/api/v1/ops/health
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({ type: 'chat', content: 'Hello!' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Angela:', data.content);
};
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://angela:angela@localhost:5432/angela

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_SECRET_KEY=your-secret-key
```

### Configuration Files

- `configs/backend_config.yaml` - Backend settings
- `configs/prometheus.yml` - Monitoring configuration
- `configs/nginx.conf` - Reverse proxy settings

## Troubleshooting

### Common Issues

**Server won't start**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Database connection failed**
```bash
# Check PostgreSQL status
docker-compose ps postgres

# Restart database
docker-compose restart postgres
```

**WebSocket not connecting**
- Ensure the backend server is running
- Check firewall settings
- Verify WebSocket URL in dashboard settings

### Logs

View logs:

```bash
# Backend logs
docker-compose logs backend

# All services
docker-compose logs -f
```

## Getting Help

- **Documentation**: See `docs/` directory
- **API Reference**: Visit `http://localhost:8000/docs` (Swagger UI)
- **Issues**: Report at GitHub Issues

## Contributing

See `docs/DEVELOPER_GUIDE.md` for contribution guidelines.
