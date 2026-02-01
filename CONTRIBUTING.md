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

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
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
python -m venv myenv

# Activate
# Windows:
myenv\Scripts\activate
# macOS/Linux:
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up credentials
cp apps/backend/config/credentials.example.json apps/backend/config/credentials.json
# Edit credentials.json with your actual credentials
```

### Frontend Setup

```bash
cd apps/frontend
npm install
npm run dev
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
   # Run tests
   python -m pytest tests/
   
   # Run linting
   python -m flake8 apps/
   
   # Check types
   python -m mypy apps/backend/
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
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_memory.py

# With coverage
python -m pytest --cov=apps/backend --cov-report=html
```

### Writing Tests

```python
import pytest
from apps.backend.memory import MemoryManager

class TestMemoryManager:
    def test_store_memory(self):
        manager = MemoryManager()
        result = manager.store("test content", {"type": "test"})
        assert result is True
        
    def test_retrieve_memory(self):
        manager = MemoryManager()
        manager.store("test content", {"type": "test"})
        memories = manager.retrieve("test", limit=1)
        assert len(memories) == 1
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
- `docs/02-api-docs/` - API documentation
- `docs/03-technical-architecture/` - Technical architecture docs
- `docs/04-deployment/` - Deployment guides
- `docs/05-development/` - Development guides
- `docs/06-project-management/` - Project management docs

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
feat(memory): add episodic memory compression

Implement compression algorithm for episodic memories
to reduce storage requirements by 60%.

Closes #123
```

## 🔍 Pull Request Process

1. **Before submitting:**
   - All tests pass
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

- **Discord**: [Join our community](https://discord.gg/catcatai)
- **Discussions**: Use GitHub Discussions for questions
- **Issues**: For bugs and feature requests

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Angela AI! 🎉
