"""
标准导入模板
包含所有常用标准库和第三方库的导入

ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
"""

# =============================================================================
# 标准库
# =============================================================================
import asyncio
import traceback
import uuid
import hashlib
import base64
import zlib
import pickle
import json
import os
import sys
import time
import math
import re
import datetime
import random
import threading
import signal
import socket
import smtplib
import pathlib
import dataclasses
import importlib
import subprocess
import logging
import csv
import configparser
import argparse
import itertools
import collections
from typing import Any, Dict, List, Optional, Tuple, Union, Set, Callable, TypeVar, Generic
from typing_extensions import Literal

# =============================================================================
# 第三方库 (必需导入)
# =============================================================================
try:
    import numpy as np
except ImportError as e:
    raise ImportError(
        "Missing required dependency: numpy\n"
        "Required version: >=1.26.4\n"
        f"Install with: pip install numpy>=1.26.4\n"
        f"Error: {e}"
    )

try:
    import torch
except ImportError as e:
    raise ImportError(
        "Missing required dependency: torch\n"
        "Required version: >=2.2.0\n"
        f"Install with: pip install torch>=2.2.0\n"
        f"Error: {e}"
    )

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "Missing required dependency: pandas\n"
        "Required version: >=2.2.0\n"
        f"Install with: pip install pandas>=2.2.0\n"
        f"Error: {e}"
    )

try:
    import yaml
except ImportError as e:
    raise ImportError(
        "Missing required dependency: PyYAML\n"
        "Required version: >=6.0.1\n"
        f"Install with: pip install pyyaml>=6.0.1\n"
        f"Error: {e}"
    )

try:
    import requests
except ImportError as e:
    raise ImportError(
        "Missing required dependency: requests\n"
        "Required version: >=2.31.0\n"
        f"Install with: pip install requests>=2.31.0\n"
        f"Error: {e}"
    )

try:
    import psutil
except ImportError as e:
    raise ImportError(
        "Missing required dependency: psutil\n"
        "Required version: >=5.9.8\n"
        f"Install with: pip install psutil>=5.9.8\n"
        f"Error: {e}"
    )

try:
    from cryptography.fernet import Fernet
except ImportError as e:
    raise ImportError(
        "Missing required dependency: cryptography\n"
        "Required version: >=42.0.0\n"
        f"Install with: pip install cryptography>=42.0.0\n"
        f"Error: {e}"
    )

try:
    import jwt
except ImportError as e:
    raise ImportError(
        "Missing required dependency: PyJWT\n"
        "Required version: >=2.9.0\n"
        f"Install with: pip install PyJWT>=2.9.0\n"
        f"Error: {e}"
    )

try:
    import speech_recognition as sr
except ImportError as e:
    raise ImportError(
        "Missing required dependency: SpeechRecognition\n"
        "Required version: >=3.10.3\n"
        f"Install with: pip install SpeechRecognition>=3.10.3\n"
        f"Error: {e}"
    )

try:
    from PIL import Image
except ImportError as e:
    raise ImportError(
        "Missing required dependency: Pillow\n"
        "Required version: >=10.3.0\n"
        f"Install with: pip install Pillow>=10.3.0\n"
        f"Error: {e}"
    )

try:
    from fastapi import FastAPI, HTTPException, APIRouter, Body, BackgroundTasks, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as e:
    raise ImportError(
        "Missing required dependency: fastapi\n"
        "Required version: >=0.109.0\n"
        f"Install with: pip install fastapi>=0.109.0\n"
        f"Error: {e}"
    )

try:
    import httpx
except ImportError as e:
    raise ImportError(
        "Missing required dependency: httpx\n"
        "Required version: >=0.26.0\n"
        f"Install with: pip install httpx>=0.26.0\n"
        f"Error: {e}"
    )

try:
    import chromadb
except ImportError as e:
    raise ImportError(
        "Missing required dependency: chromadb\n"
        "Required version: >=0.5.0\n"
        f"Install with: pip install chromadb>=0.5.0\n"
        f"Error: {e}"
    )

# =============================================================================
# 第三方库 (可选导入)
# =============================================================================
try:
    import tensorflow as tf
except ImportError:
    tf = None
    # Note: TensorFlow is optional because PyTorch is the primary ML framework

try:
    import redis.asyncio as redis
except ImportError:
    redis = None
    # Note: Redis is optional for caching

try:
    import cv2
except ImportError:
    cv2 = None
    # Note: OpenCV is optional for computer vision features

try:
    import jieba
except ImportError:
    jieba = None
    # Note: jieba is optional for Chinese text segmentation

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    hf_hub_download = None
    # Note: huggingface_hub is optional for model hub access

# =============================================================================
# 本地导入
# =============================================================================
try:
    from .logger import get_logger
except ImportError:
    def get_logger(name: str):
        return logging.getLogger(name)

logger = get_logger(__name__)

# =============================================================================
# 类型别名
# =============================================================================
JSONType = Dict[str, Any]
AnyDict = Dict[str, Any]
AnyList = List[Any]
OptionalDict = Optional[Dict[str, Any]]
OptionalList = Optional[List[Any]]

# =============================================================================
# 常量
# =============================================================================
DEFAULT_ENCODING = 'utf-8'
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3