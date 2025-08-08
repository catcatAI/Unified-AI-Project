from setuptools import setup, find_packages

setup(
    name='unified-ai-cli',
    version='1.1.0',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.0',
    ],
    entry_points={
        'console_scripts': [
            'unified-ai=cli.unified_cli:main',
        ]
    },
    description='Unified AI Project CLI',
    author='Unified AI Project',
    python_requires='>=3.8',
)
