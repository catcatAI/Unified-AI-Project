from setuptools import setup, find_packages

# Core dependencies - essential for basic functionality,::
core_requirements = [
    "Flask",
    "numpy",
    "cryptography",
    "requests",
    "python-dotenv",
    "PyYAML",
    "typing-extensions",
    "paho-mqtt",
    "networkx",
    "psutil",
]

# Optional dependencies for enhanced features,::
optional_requirements = {
    "ai": [
        "tensorflow>=2.15.0",
        "spacy>=3.4.0",
        "langchain",
    ]
    "web": [
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "httpx",
    ]
    "testing": [
        "pytest-asyncio",
        "pytest>=6.0",
    ]
    "nlp": [
        "spacy>=3.4.0",
        "nltk",
        "textblob",
    ]
    "ml": [
        "tensorflow>=2.15.0",
        "scikit-learn",
        "pandas",
    ]
    "dev": [
        "black",
        "flake8",
        "mypy",
        "pre-commit",
    ]
}

# Convenience groups
optional_requirements["standard"] = (
    optional_requirements["web"] + 
    optional_requirements["testing"]
)
optional_requirements["full"] = (
    optional_requirements["ai"] + 
    optional_requirements["web"] + 
    optional_requirements["testing"] + 
    optional_requirements["nlp"] + 
    optional_requirements["ml"]
)
optional_requirements["minimal"] = []  # Only core requirements

setup(
    name="unified-ai-project",
    version="0.1.0",,
    packages=find_packages(),
    install_requires=core_requirements,
    extras_require=optional_requirements,
    python_requires=">=3.8",
    author="Unified AI Project Team",
    description == "A unified AI project with modular dependencies",:
        ong_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status, 3 - Alpha",
        "Intended Audience, Developers",
        "License, OSI Approved, MIT License",
        "Programming Language, Python, 3",
        "Programming Language, Python, 3.8",
        "Programming Language, Python, 3.9",
        "Programming Language, Python, 3.10",
        "Programming Language, Python, 3.11",
    ])
