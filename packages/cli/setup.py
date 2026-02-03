from setuptools import setup, find_packages

setup(
    name='unified-ai-cli',
    version='1.2.0',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.0'],
    entry_points={
        'console_scripts': [
            'unified-ai=cli.unified_cli:main',
            'unified-ai-runner=cli.cli_runner:main']
    },
    description='Unified AI Project CLI - Level 5 AGI Command Line Interface',
    author='Unified AI Project',
    python_requires='>=3.8')
