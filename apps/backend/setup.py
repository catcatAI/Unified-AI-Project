from setuptools import setup, find_packages

# Core dependencies - synced with pyproject.toml (source of truth)
core_requirements = [
    "numpy>=1.21.0",
    "cryptography>=41.0.0",
    "requests>=2.25.0",
    "python-dotenv>=0.19.0",
    "PyYAML>=6.0",
    "typing-extensions>=4.0.0",
    "paho-mqtt>=1.6.0",
    "networkx>=2.6.0",
    "psutil>=5.8.0",
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "httpx>=0.23.0",
    "rich>=13.0.0",
    "click>=8.0.0",
    "tqdm>=4.64.0",
    "aiohttp>=3.8.0",
    "Pillow>=9.0.0",
    "faiss-cpu>=1.7.0",
    "sentence-transformers>=2.2.0",
    "gmqtt>=0.7.0",
    "firebase-admin>=6.0.0",
    "edge-tts>=6.1.9",
    "openai-whisper>=20230124",
    "pyautogui>=0.9.54",
    "pynput>=1.7.6",
    "pygetwindow>=0.0.9",
    "pytesseract>=0.3.10",
    "websockets>=10.4",
    "py-cpuinfo>=9.0.0",
    "pandas",
    "scikit-learn",
]

# Optional dependencies for enhanced features
optional_requirements = {
    "ai": [
        "tensorflow>=2.15.0",
        "spacy>=3.4.0",
        "sentence-transformers>=2.2.0",
        "huggingface-hub",
        "transformers",
    ],
    "web": [
        "uvicorn[standard]",
        "pydantic",
        "httpx>=0.23.0",
    ],
    "testing": [
        "pytest>=6.0",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-timeout",
        "aiounittest",
        "astunparse",
    ],
    "nlp": [
        "spacy>=3.4.0",
        "nltk",
        "textblob",
    ],
    "ml": [
        "tensorflow>=2.15.0",
        "scikit-learn",
        "pandas",
    ],
    "dev": [
        "black",
        "flake8",
        "mypy",
        "isort",
        "pre-commit",
    ],
    "game": [
        "pygame",
        "PyQt5",
    ],
    "installer": [
        "PyQt5",
        "pyshortcuts",
        "secret-sharing",
        "qrcode",
    ],
}

# Convenience groups
optional_requirements["standard"] = (
    optional_requirements["web"] +
    optional_requirements["testing"] +
    ["chromadb"]
)
optional_requirements["full"] = (
    optional_requirements["ai"] +
    optional_requirements["web"] +
    optional_requirements["testing"] +
    optional_requirements["nlp"] +
    optional_requirements["ml"] +
    optional_requirements["game"]
)
optional_requirements["minimal"] = []  # Only core requirements

setup(
    name="unified-ai-project",
    version="7.5.0-dev",
    packages=find_packages(),
    install_requires=core_requirements,
    extras_require=optional_requirements,
    python_requires=">=3.8",
    author="Unified AI Project Team",
    description="A unified AI project with modular dependencies",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ])
