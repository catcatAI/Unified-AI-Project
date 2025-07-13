from setuptools import setup, find_packages

setup(
    name="unified-ai-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Flask",
        "numpy",
        "cryptography",
        "requests",
        "python-dotenv",
        "PyYAML",
        "typing-extensions",
        "langchain",
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "httpx",
        "psutil",
        "spacy",
        "networkx",
        "paho-mqtt",
        "pytest-asyncio",
        "tensorflow==2.16.1"
    ],
)
