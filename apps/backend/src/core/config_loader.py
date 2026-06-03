#!/usr/bin/env python3
"""
Angela AI - Configuration Loader
配置加载器

安全地加载和访问应用配置，提供类型安全的配置访问。
支持 YAML 多文件读取、热重载、Authority + Learned 双层配置合并。
"""

import os
import json
import copy
import yaml
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional