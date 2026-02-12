# Contributing to Angela AI

Thank you for your interest in contributing to Angela AI! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code of conduct.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Git
- Live2D Cubism SDK (for desktop pet features)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Unified-AI-Project.git
cd Unified-AI-Project

# Add upstream remote
git remote add upstream https://github.com/catcatAI/Unified-AI-Project.git
```

## 💻 Development Setup

### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up credentials
cp .env.example .env
# Edit .env with your actual credentials
```

### Frontend Setup

```bash
cd apps/desktop-app/electron_app
npm install

# For web dashboard
cd apps/frontend-dashboard
npm install
```

### Start Development Environment

```bash
# Using unified launcher (recommended)
./start_angela_complete.sh

# Or manually:
# Backend
cd apps/backend
python3 -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000

# Desktop App
cd apps/desktop-app/electron_app
npm start
```

## 🛠️ How to Contribute

### Reporting Bugs

1. Check if the bug is already reported in [Issues](https://github.com/catcatAI/Unified-AI-Project/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)
   - Screenshots/logs if applicable

### Suggesting Features

1. Open an issue with the "Feature Request" label
2. Describe the feature and its use case
3. Explain why it would be valuable

### Contributing Code

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**
   - Follow coding standards
   - Add tests for new functionality
   - Update documentation

3. **Test your changes**
   ```bash
   # Run comprehensive test
   python3 comprehensive_test.py
   
   # Run pytest tests
   python3 -m pytest tests/
   
   # Run linting
   python3 -m flake8 apps/backend/src/
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Go to GitHub and create a PR
   - Fill in the PR template
   - Link related issues

## 📝 Coding Standards

### Python

- Follow [PEP 8](https://pep8.org/)
- Use type hints
- Maximum line length: 100 characters
- Use docstrings (Google style)

```python
def process_user_input(
    user_id: str,
    message: str,
    context: Optional[Dict] = None
) -> Response:
    """Process user input and generate response.
    
    Args:
        user_id: Unique identifier for the user
        message: Input message from user
        context: Optional conversation context
        
    Returns:
        Response object containing the AI's reply
        
    Raises:
        ValueError: If user_id is empty
    """
```

### JavaScript/TypeScript

- Use ESLint configuration
- Prefer const/let over var
- Use async/await for asynchronous code
- Document complex functions

### Documentation

- Update README.md if adding new features
- Add docstrings to all public functions
- Update API documentation for changes
- Include examples in documentation

## 🧪 Testing

### Running Tests

```bash
# Comprehensive test suite
python3 comprehensive_test.py

# pytest tests
python3 -m pytest tests/

# Specific test file
python3 -m pytest tests/ai/test_ham_importance_scorer.py

# With coverage
python3 -m pytest --cov=apps/backend/src --cov-report=html
```

### Writing Tests

```python
import pytest
from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer

class TestImportanceScorer:
    @pytest.fixture
    def scorer(self):
        return ImportanceScorer()
    
    @pytest.mark.asyncio
    async def test_basic_score(self, scorer):
        metadata = {}
        score = await scorer.calculate("普通消息", metadata)
        assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_keyword_boost(self, scorer):
        score_urgent = await scorer.calculate("这是一个urgent消息", {})
        score_normal = await scorer.calculate("这是一个普通消息", {})
        assert score_urgent > score_normal
```

## 📚 Documentation

### Code Documentation

- All modules should have module docstrings
- All public classes need class docstrings
- All public methods need method docstrings
- Use type hints throughout

### Project Documentation

Located in `docs/` directory:
- `docs/00-overview/` - Project overview and vision
- `docs/01-summaries-and-reports/` - Project reports and summaries
- `docs/02-game-design/` - Game design documentation
- `docs/03-technical-architecture/` - Technical architecture docs
- `docs/04-advanced-concepts/` - Advanced concepts
- `docs/05-development/` - Development guides
- `docs/06-project-management/` - Project management docs
- `docs/api/` - API documentation
- `docs/architecture/` - Architecture documentation
- `docs/deployment/` - Deployment guides
- `docs/developer-guide/` - Developer guides
- `docs/testing/` - Testing guides
- `docs/user-guide/` - User guides

### API Endpoints

Main API endpoints:

**Backend API (FastAPI)**
- `GET /health` - Health check
- `POST /angela/chat` - Chat endpoint (uses LLM)
- `POST /dialogue` - Dialogue management
- `GET /status` - System status
- WebSocket `/ws` - Real-time communication

**Key Services**
- LLM Service: Multi-backend support (Ollama, OpenAI, Anthropic)
- HAM Memory System: Hierarchical associative memory
- AI Agents: 15 specialized agents
- Live2D Manager: Character rendering and animation

## 💬 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, etc.

Examples:
```
feat(ham): add episodic memory compression

Implement compression algorithm for episodic memories
to reduce storage requirements by 60%.

Closes #123

fix(audio): resolve speech recognition timeout

Add proper timeout handling for speech recognition
to prevent infinite waiting on audio input.

refactor(logging): upgrade to enhanced logger system

Replace console statements with AngelaLogger for better
log management and filtering.
```

## 🔍 Pull Request Process

1. **Before submitting:**
   - All tests pass (`python3 comprehensive_test.py`)
   - Code follows style guidelines
   - Documentation updated
   - Commit messages follow convention

2. **PR Template:**
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Screenshots (if UI changes)

3. **Review Process:**
   - At least one maintainer review required
   - Address review comments
   - Keep PR focused and small

4. **After merge:**
   - Delete your branch
   - Update related issues

## 🆘 Getting Help

- **Documentation**: Check `docs/` directory for detailed guides
- **Issues**: For bugs and feature requests

## 🏆 Recognition

Contributors will be:
- Listed in release notes
- Credited in documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Angela AI! 🎉
