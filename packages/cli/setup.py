from setuptools import find_packages, setup

setup(
    name="unified-cli",
    version="7.5.0-dev",
    description="Unified AI Project CLI",
    packages=find_packages(where="."),
    package_dir={"": "."},
    install_requires=[
        "requests>=2.28",
        "httpx>=0.24",
    ],
    extras_require={
        "monitoring": ["psutil>=5.9"],
    },
    entry_points={
        "console_scripts": [
            "unified-ai=cli.unified_cli:main",
        ],
    },
    python_requires=">=3.10",
)
