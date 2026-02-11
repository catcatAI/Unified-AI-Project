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
# 第三方库 (可选导入)
# =============================================================================
try:
    import numpy as np
except ImportError:
    np = None

try:
    import torch
except ImportError:
    torch = None

try:
    import tensorflow as tf
except ImportError:
    tf = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

try:
    import jwt
except ImportError:
    jwt = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import jieba
except ImportError:
    jieba = None

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    hf_hub_download = None

try:
    from fastapi import FastAPI, HTTPException, APIRouter, Body, BackgroundTasks, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    FastAPI = None
    HTTPException = None
    APIRouter = None
    Body = None
    BackgroundTasks = None
    WebSocket = None
    WebSocketDisconnect = None
    CORSMiddleware = None

try:
    import httpx
except ImportError:
    httpx = None

try:
    import chromadb
except ImportError:
    chromadb = None

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