# Angela AI v6.2.0 - 结构化修复任务链

## 📋 任务链概览

本文档定义了 Angela AI 项目从当前状态 (v6.2.0,
99.2% 完成) 到完全生产就绪状态的完整修复路径。

**总问题数**: ~350  
**预计总时间**: 2-4 周  
**关键里程碑**: 5 个阶段

---

## 🎯 任务链矩阵

```
┌─────────────────────────────────────────────────────────────────┐
│                    Angela AI 修复任务链                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段 1: CRITICAL          ───►  阶段 2: HIGH                  │
│  [14 个问题]                       [199 个问题]                   │
│  时间: 1-2 小时                    时间: 24-48 小时              │
│  优先级: 🔴 最高                    优先级: 🟠 高                 │
│                                                                 │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────────┐                                               │
│  │  语法错误修复   │                                               │
│  │  安全漏洞修复   │                                               │
│  │  导入错误修复   │                                               │
│  └─────────────────┘                                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段 3: MEDIUM          ───►  阶段 4: LOW                     │
│  [61 个问题]                       [72+ 个问题]                   │
│  时间: 5-7 天                      时间: 2-4 周                   │
│  优先级: 🟡 中                      优先级: 🟢 低                 │
│                                                                 │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────────┐                                               │
│  │  错误处理改进   │                                               │
│  │  性能优化       │                                               │
│  │  代码规范统一   │                                               │
│  └─────────────────┘                                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段 5: 测试与验证                                              │
│  [持续进行]                                                       │
│  时间: 贯穿整个修复过程                                           │
│  优先级: 🔴 最高                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 详细任务链

### 🔴 阶段 1: CRITICAL - 紧急修复

**时间**: 1-2 小时  
**阻塞**: 阻止所有其他工作  
**完成标准**: 0 CRITICAL 错误，所有文件可正常导入

#### 任务组 1.1: Python 语法错误修复 (12个)

```
任务编号: P-CRITICAL-001 至 P-CRITICAL-012
优先级: P0 (最高)
预计时间: 30 分钟
依赖: 无
```

**任务列表**:

| ID             | 文件路径                                                  | 行号 | 问题描述     | 修复方案       | 状态      |
| -------------- | --------------------------------------------------------- | ---- | ------------ | -------------- | --------- |
| P-CRITICAL-001 | `shared/utils/env_utils.py`                               | 2    | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-002 | `shared/network_resilience.py`                            | 83   | 未终止字符串 | 修复引号闭合   | ⏳ 待开始 |
| P-CRITICAL-003 | `shared/types/mappable_data_object.py`                    | 3    | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-004 | `core/hsp/types_fixed.py`                                 | 9    | 无效语法     | 移除或修正注释 | ⏳ 待开始 |
| P-CRITICAL-005 | `core/error/error_handler.py`                             | 8    | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-006 | `core/shared/utils/cleanup_utils.py`                      | 2    | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-007 | `core/shared/key_manager.py`                              | 6    | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-008 | `core/shared/types/common_types.py`                       | 61   | 类型提示错误 | 修正 Literal[] | ⏳ 待开始 |
| P-CRITICAL-009 | `core/logging/enterprise_logger.py`                       | 6    | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-010 | `core/metacognition/metacognitive_capabilities_engine.py` | 16   | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-011 | `core/knowledge/unified_knowledge_graph.py`               | 15   | 不完整导入   | 移除或补全导入 | ⏳ 待开始 |
| P-CRITICAL-012 | `core/shared/types/mappable_data_object.py`               | 3    | 重复导入错误 | 移除或补全导入 | ⏳ 待开始 |

**执行步骤**:

```bash
# 步骤 1: 批量修复不完整导入
find apps/backend/src -name "*.py" -exec sed -i '/^from tests\.tools\.test_tool_dispatcher_logging import$/d' {} \;

# 步骤 2: 修复未终止字符串
sed -i '83s/self.logger.info("Circuit Breaker,$/self.logger.info("Circuit Breaker, State changed to HALF_OPEN..."/' \
  apps/backend/src/shared/network_resilience.py

# 步骤 3: 修复类型提示
# 手动编辑 core/shared/types/common_types.py:61
# 将 status: Literal[] 改为 status: Literal["success", "failure", ...]

# 步骤 4: 验证修复
find apps/backend/src -name "*.py" -exec python3 -m py_compile {} \;
```

**验证标准**:

- ✅ `python3 -m py_compile` 无错误
- ✅ 所有文件可以正常导入
- ✅ 无语法错误

---

#### 任务组 1.2: JavaScript 语法错误修复 (2个)

```
任务编号: J-CRITICAL-001 至 J-CRITICAL-002
优先级: P0 (最高)
预计时间: 15 分钟
依赖: 无
```

**任务列表**:

| ID             | 文件路径                      | 行号    | 问题描述     | 修复方案     | 状态      |
| -------------- | ----------------------------- | ------- | ------------ | ------------ | --------- |
| J-CRITICAL-001 | `js/live2d-cubism-wrapper.js` | 243-247 | 重复闭合括号 | 移除重复的 } | ⏳ 待开始 |
| J-CRITICAL-002 | `main.js`                     | 145-210 | 路径遍历漏洞 | 添加路径验证 | ⏳ 待开始 |

**执行步骤**:

```javascript
// 修复 J-CRITICAL-001: 移除重复的闭合括号
// 文件: js/live2d-cubism-wrapper.js:243-247

// 修复前 (错误)
async loadModel(settings) {
    // ... 代码 ...
    this.isLoaded = true;
    return true;
}        // Line 243 - 第一个闭合括号
        this.isLoaded = false;  // 这行会被跳过
        throw error;
    }
}        // Line 247 - 重复的闭合括号

// 修复后
async loadModel(settings) {
    const modelPath = settings.modelPath;
    console.log('[loadModel] Loading from:', modelPath);

    try {
        // ... 模型加载代码 ...

        this.isLoaded = true;
        console.log('[loadModel] SUCCESS: Live2D model loaded successfully');
        return true;
    } catch (error) {
        console.error('[loadModel] FAILED:', error.message);
        this.isLoaded = false;
        throw error;
    }
}

// 修复 J-CRITICAL-002: 添加路径验证
// 文件: main.js:145-210

// 修复前
protocol.registerFileProtocol('local', (request, callback) => {
    let urlPath = request.url;
    // ... 无验证的路径处理 ...
    const filePath = require('path').resolve(require('path').normalize(urlPath));
    if (require('fs').existsSync(filePath)) {
        callback({ path: filePath });  // 危险！
    }
});

// 修复后
const ALLOWED_DIRECTORIES = [
    require('path').join(__dirname, 'resources'),
    require('path').join(__dirname, 'resources/models'),
    require('path').join(__dirname, 'data')
];

protocol.registerFileProtocol('local', (request, callback) => {
    const url = new URL(request.url);
    let urlPath = url.pathname;

    try {
        urlPath = decodeURIComponent(urlPath);
    } catch (e) {
        console.warn('[Main] Failed to decode URL:', urlPath);
        return callback({ error: -2 }); // Failed to decode
    }

    // 移除 local: 前缀
    if (urlPath.startsWith('/')) {
        urlPath = urlPath.substring(1);
    }

    // 规范化路径
    const filePath = require('path').resolve(require('path').normalize(urlPath));

    // 验证路径是否在允许的目录内
    const isAllowed = ALLOWED_DIRECTORIES.some(allowedDir => {
        const relativePath = require('path').relative(allowedDir, filePath);
        return !relativePath.startsWith('..');
    });

    if (!isAllowed) {
        console.warn('[Main] Path traversal attempt blocked:', filePath);
        return callback({ error: -3 }); // Access denied
    }

    if (require('fs').existsSync(filePath)) {
        callback({ path: filePath });
    } else {
        callback({ error: -6 }); // File not found
    }
});
```

**验证标准**:

- ✅ ESLint 无错误
- ✅ Live2D 可以正常加载
- ✅ 路径遍历测试通过

---

#### 任务组 1.3: 验证语法修复

```
任务编号: V-CRITICAL-001
优先级: P0 (最高)
预计时间: 15 分钟
依赖: 任务组 1.1, 1.2
```

**执行步骤**:

```bash
# 步骤 1: Python 语法验证
cd /home/cat/桌面/Unified-AI-Project
python3 -m py_compile apps/backend/src/**/*.py 2>&1 | tee syntax_errors.log

# 步骤 2: JavaScript 语法验证
cd apps/desktop-app/electron_app
npx eslint js/**/*.js --format json 2>&1 | tee eslint_errors.json

# 步骤 3: 导入测试
python3 -c "
import sys
sys.path.insert(0, 'apps/backend/src')
try:
    from services.main_api_server import app
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

# 步骤 4: 生成验证报告
cat > phase1_verification.md << EOF
# Phase 1 验证报告

## Python 语法验证
$(cat syntax_errors.log | wc -l) 个错误

## JavaScript 语法验证
$(cat eslint_errors.json | jq '.errorCount') 个错误

## 导入测试
$(python3 -c "import sys; sys.path.insert(0, 'apps/backend/src'); from services.main_api_server import app" && echo "✅ 通过" || echo "❌ 失败")

## 状态
$(if [ $(cat syntax_errors.log | wc -l) -eq 0 ] && [ $(cat eslint_errors.json | jq '.errorCount') -eq 0 ]; then echo "✅ Phase 1 完成"; else echo "❌ Phase 1 失败"; fi)
EOF
```

**验证标准**:

- ✅ 0 Python 语法错误
- ✅ 0 JavaScript 语法错误
- ✅ 所有导入成功
- ✅ 生成验证报告

---

### 🟠 阶段 2: HIGH - 高优先级修复

**时间**: 24-48 小时  
**依赖**: 阶段 1 完成  
**完成标准**: 0 HIGH 级别安全问题，0 内存泄漏

#### 任务组 2.1: Python 导入错误修复 (178个)

```
任务编号: P-HIGH-001
优先级: P1 (高)
预计时间: 8-12 小时
依赖: 阶段 1 完成
```

**任务分解**:

**子任务 2.1.1: 创建标准导入模板**

```python
# apps/backend/src/shared/standard_imports.py
"""
标准导入模板
包含所有常用标准库和第三方库的导入
"""

# 标准库
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
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import Literal

# 第三方库
import numpy as np
import torch
import tensorflow as tf
import pandas as pd
import yaml
import requests
import redis.asyncio as redis
import psutil
from cryptography.fernet import Fernet
import jwt
import speech_recognition as sr
from PIL import Image
import cv2
import jieba
from huggingface_hub import hf_hub_download

# 本地导入
from .logger import get_logger

logger = get_logger(__name__)
```

**子任务 2.1.2: 批量添加缺失导入**

```bash
# 创建导入修复脚本
cat > fix_imports.py << 'EOF'
#!/usr/bin/env python3
import re
import os
from pathlib import Path

# 需要添加的导入映射
IMPORT_MAP = {
    'asyncio': 'import asyncio',
    'traceback': 'import traceback',
    'uuid': 'import uuid',
    'hashlib': 'import hashlib',
    'numpy': 'import numpy as np',
    'torch': 'import torch',
    'tensorflow': 'import tensorflow as tf',
    'yaml': 'import yaml',
    'secrets': 'import secrets',
    'jwt': 'import jwt',
    'pandas': 'import pandas as pd',
    'requests': 'import requests',
    'redis': 'import redis',
    'psutil': 'import psutil',
    'base64': 'import base64',
    'zlib': 'import zlib',
    'pickle': 'import pickle',
    'jieba': 'import jieba',
    'typing': 'from typing import Any, Dict, List, Optional',
}

def detect_missing_imports(file_path):
    """检测文件中缺失的导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    missing = []
    for name, import_stmt in IMPORT_MAP.items():
        # 检查是否使用了该模块但未导入
        if re.search(r'\b' + name + r'\b', content):
            if not re.search(r'^' + re.escape(import_stmt), content, re.MULTILINE):
                missing.append((name, import_stmt))

    return missing

def fix_file_imports(file_path):
    """修复文件的导入"""
    missing = detect_missing_imports(file_path)

    if not missing:
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 在文件开头添加缺失的导入
    import_block = '\n'.join(stmt for _, stmt in missing)

    # 找到第一个非注释、非空行
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('#'):
            insert_pos = i
            break

    # 插入导入
    lines.insert(insert_pos, import_block)
    lines.insert(insert_pos + 1, '')

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return True

if __name__ == '__main__':
    base_dir = Path('apps/backend/src')

    fixed_count = 0
    for py_file in base_dir.rglob('*.py'):
        if fix_file_imports(py_file):
            print(f'Fixed imports in: {py_file}')
            fixed_count += 1

    print(f'\nTotal files fixed: {fixed_count}')
EOF

chmod +x fix_imports.py
python3 fix_imports.py
```

**子任务 2.1.3: 更新 requirements.txt**

```bash
# 更新依赖列表
cat > apps/backend/requirements.txt << 'EOF'
# 核心框架
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# AI/ML
numpy>=1.24.0
torch>=2.0.0
tensorflow>=2.14.0
scikit-learn>=1.3.0
pandas>=2.0.0
transformers>=4.35.0
huggingface-hub>=0.18.0

# 数据库
chromadb>=0.4.18
sqlalchemy>=2.0.23
redis>=5.0.0

# 网络通信
websockets>=12.0
requests>=2.31.0
aiohttp>=3.9.0

# 安全
cryptography>=41.0.0
pyjwt>=2.8.0
python-multipart>=0.0.6

# 音频处理
speechrecognition>=3.10.0
pyaudio>=0.2.14

# 图像处理
Pillow>=10.1.0
opencv-python>=4.8.1

# 自然语言处理
jieba>=0.42.1
openai>=1.3.0
anthropic>=0.7.0

# 系统监控
psutil>=5.9.0
GPUtil>=1.4.0

# 配置管理
pyyaml>=6.0.1
python-dotenv>=1.0.0

# 日志
loguru>=0.7.2

# 其他
orjson>=3.9.10
EOF

# 安装依赖
pip install -r apps/backend/requirements.txt
```

**验证标准**:

- ✅ 所有导入错误已修复
- ✅ `requirements.txt` 已更新
- ✅ 所有依赖可正常安装

---

#### 任务组 2.2: 安全问题修复 (20个)

```
任务编号: P-HIGH-002 至 P-HIGH-021
优先级: P1 (高)
预计时间: 8-12 小时
依赖: 阶段 1 完成
```

**任务列表**:

| ID         | 文件路径                                 | 问题描述            | 修复方案                 | 状态      |
| ---------- | ---------------------------------------- | ------------------- | ------------------------ | --------- |
| P-HIGH-002 | `core/config/system_config.py`           | MQTT 密码直接使用   | 使用环境变量 + 验证      | ⏳ 待开始 |
| P-HIGH-003 | `core/desktop/key_manager_gui.py`        | API 密钥需加密存储  | 实现密钥管理器           | ⏳ 待开始 |
| P-HIGH-004 | `core/security/auth_middleware.py`       | 密钥存储需更安全    | 使用 Fernet 加密         | ⏳ 待开始 |
| P-HIGH-005 | `core/shared/key_manager.py`             | 硬编码演示密钥      | 移除硬编码，生成随机密钥 | ⏳ 待开始 |
| P-HIGH-006 | `integrations/confluence_integration.py` | 硬编码模拟令牌      | 使用环境变量             | ⏳ 待开始 |
| P-HIGH-007 | `integrations/jira_integration.py`       | 硬编码模拟令牌      | 使用环境变量             | ⏳ 待开始 |
| J-HIGH-001 | `js/security-manager.js`                 | Scrypt 盐硬编码     | 使用随机盐               | ⏳ 待开始 |
| J-HIGH-002 | `js/security-manager.js`                 | HTTP 请求无证书验证 | 添加证书验证             | ⏳ 待开始 |
| J-HIGH-003 | `js/live2d-cubism-wrapper.js`            | CDN 无 SRI 哈希     | 添加 SRI 哈希            | ⏳ 待开始 |
| J-HIGH-004 | `js/app.js`                              | Key C 使用 HTTP     | 改用 HTTPS               | ⏳ 待开始 |
| J-HIGH-005 | `js/main.js`                             | 路径遍历漏洞        | 添加路径验证             | ⏳ 待开始 |
| ...        | ...                                      | ...                 | ...                      | ...       |

**修复示例: 密钥管理器**

```python
# apps/backend/src/core/security/key_manager.py
"""
安全密钥管理器
用于生成、存储和检索加密密钥
"""
import os
import json
import secrets
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import yaml

class KeyManager:
    """安全密钥管理器"""

    def __init__(self, key_file: str = "data/security/keys.json"):
        self.key_file = Path(key_file)
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self._keys: Dict[str, str] = {}
        self._load_keys()

    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """从密码派生加密密钥"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password)

    def _load_keys(self):
        """加载加密的密钥"""
        if not self.key_file.exists():
            return

        try:
            with open(self.key_file, 'r') as f:
                data = json.load(f)

            # 从环境变量获取主密钥
            master_key = os.getenv('ANGELA_MASTER_KEY')
            if not master_key:
                raise ValueError("ANGELA_MASTER_KEY environment variable not set")

            # 解密密钥
            salt = bytes.fromhex(data['salt'])
            key = self._derive_key(master_key.encode(), salt)
            fernet = Fernet(key)

            decrypted = fernet.decrypt(data['encrypted'].encode())
            self._keys = json.loads(decrypted.decode())

        except Exception as e:
            print(f"Warning: Failed to load keys: {e}")
            self._keys = {}

    def _save_keys(self):
        """保存加密的密钥"""
        try:
            # 从环境变量获取主密钥
            master_key = os.getenv('ANGELA_MASTER_KEY')
            if not master_key:
                raise ValueError("ANGELA_MASTER_KEY environment variable not set")

            # 生成随机盐
            salt = secrets.token_bytes(16)

            # 派生加密密钥
            key = self._derive_key(master_key.encode(), salt)
            fernet = Fernet(key)

            # 加密密钥
            encrypted = fernet.encrypt(json.dumps(self._keys).encode())

            # 保存
            data = {
                'salt': salt.hex(),
                'encrypted': encrypted.decode()
            }

            with open(self.key_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error saving keys: {e}")

    def generate_key(self, key_name: str, length: int = 32) -> str:
        """生成并存储新密钥"""
        key = secrets.token_urlsafe(length)
        self._keys[key_name] = key
        self._save_keys()
        return key

    def get_key(self, key_name: str) -> Optional[str]:
        """获取密钥"""
        return self._keys.get(key_name)

    def set_key(self, key_name: str, key_value: str):
        """设置密钥"""
        self._keys[key_name] = key_value
        self._save_keys()

    def delete_key(self, key_name: str):
        """删除密钥"""
        if key_name in self._keys:
            del self._keys[key_name]
            self._save_keys()

    def rotate_key(self, key_name: str) -> str:
        """轮换密钥"""
        new_key = secrets.token_urlsafe(32)
        self._keys[key_name] = new_key
        self._save_keys()
        return new_key

# 使用示例
if __name__ == '__main__':
    key_manager = KeyManager()

    # 生成 A/B/C 密钥
    key_a = key_manager.generate_key('key_a', 32)
    key_b = key_manager.generate_key('key_b', 32)
    key_c = key_manager.generate_key('key_c', 32)

    print(f"Key A: {key_a[:10]}...")
    print(f"Key B: {key_b[:10]}...")
    print(f"Key C: {key_c[:10]}...")
```

**修复示例: JavaScript SRI 哈希**

```javascript
// js/live2d-cubism-wrapper.js
// 添加 SRI (Subresource Integrity) 哈希验证

const CDN_SOURCES = {
  'cubism-sdk': {
    url: 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
    integrity: 'sha384-abcdefghijklmnopqrstuvwxyz123456', // 实际使用时需要生成正确的哈希
    crossOrigin: 'anonymous',
  },
  'cubism-js': {
    url: 'https://cubism.live2d.com/sdk-web/live2dframework/live2dframework.min.js',
    integrity: 'sha384-abcdefghijklmnopqrstuvwxyz123456',
    crossOrigin: 'anonymous',
  },
}

async function loadScriptWithSRI(source) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = source.url
    script.integrity = source.integrity
    script.crossOrigin = source.crossOrigin

    script.onload = () => resolve(script)
    script.onerror = () => reject(new Error(`Failed to load ${source.url}`))

    document.head.appendChild(script)
  })
}

// 使用
try {
  await loadScriptWithSRI(CDN_SOURCES['cubism-sdk'])
  await loadScriptWithSRI(CDN_SOURCES['cubism-js'])
  console.log('[Live2D] All scripts loaded with SRI verification')
} catch (error) {
  console.error('[Live2D] Failed to load scripts:', error)
  throw error
}
```

**验证标准**:

- ✅ 所有硬编码密钥已移除
- ✅ 密钥管理系统已实现
- ✅ SRI 哈希已添加
- ✅ 路径遍历漏洞已修复
- ✅ 安全扫描通过

---

#### 任务组 2.3: JavaScript 性能问题修复 (5个)

```
任务编号: J-HIGH-006 至 J-HIGH-010
优先级: P1 (高)
预计时间: 4-6 小时
依赖: 阶段 1 完成
```

**修复示例: 纹理缓存**

```javascript
// js/live2d-cubism-wrapper.js
// 实现纹理缓存

class TextureCache {
  constructor(maxSize = 100) {
    this.cache = new Map()
    this.maxSize = maxSize
    this.canvasPool = []
  }

  getCanvas(width, height) {
    // 从池中获取 Canvas
    for (let canvas of this.canvasPool) {
      if (canvas.width === width && canvas.height === height) {
        this.canvasPool = this.canvasPool.filter((c) => c !== canvas)
        return canvas
      }
    }
    // 创建新 Canvas
    return document.createElement('canvas')
  }

  releaseCanvas(canvas) {
    // 将 Canvas 返回到池中
    if (this.canvasPool.length < 10) {
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      this.canvasPool.push(canvas)
    }
  }

  get(key) {
    return this.cache.get(key)
  }

  set(key, texture) {
    if (this.cache.size >= this.maxSize) {
      // LRU 淘汰
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }
    this.cache.set(key, texture)
  }

  clear() {
    this.cache.clear()
    this.canvasPool = []
  }
}

// 在 Live2DCubismWrapper 中使用
class Live2DCubismWrapper {
  constructor() {
    this.textureCache = new TextureCache()
  }

  // 原始的低效方法
  _scaleTextureOld(texture, targetWidth, targetHeight) {
    const canvas = document.createElement('canvas') // 每次都创建新 Canvas
    canvas.width = targetWidth
    canvas.height = targetHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(texture, 0, 0, targetWidth, targetHeight)
    return canvas
  }

  // 优化后的方法
  _scaleTexture(texture, targetWidth, targetHeight) {
    const cacheKey = `${texture.src}_${targetWidth}_${targetHeight}`
    const cached = this.textureCache.get(cacheKey)

    if (cached) {
      return cached
    }

    // 从池中获取 Canvas
    const canvas = this.textureCache.getCanvas(targetWidth, targetHeight)
    const ctx = canvas.getContext('2d')
    ctx.drawImage(texture, 0, 0, targetWidth, targetHeight)

    // 缓存结果
    this.textureCache.set(cacheKey, canvas)

    return canvas
  }

  destroy() {
    this.textureCache.clear()
    // ... 其他清理代码
  }
}
```

**验证标准**:

- ✅ 内存泄漏已修复
- ✅ 性能提升 50%+
- ✅ 纹理加载速度提升

---

### 🟡 阶段 3: MEDIUM - 中优先级修复

**时间**: 5-7 天  
**依赖**: 阶段 2 完成  
**完成标准**: 0 裸异常捕获，所有类型提示正确

#### 任务组 3.1: 错误处理改进 (23个)

```
任务编号: P-MEDIUM-001 至 P-MEDIUM-023
优先级: P2 (中)
预计时间: 2-3 天
依赖: 阶段 2 完成
```

**修复模板**:

```python
# 统一错误处理模板
from typing import Optional, Type, Union, Callable
import functools
import logging

logger = logging.getLogger(__name__)

class AngelaError(Exception):
    """Angela AI 基础异常类"""
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class ConfigurationError(AngelaError):
    """配置错误"""
    pass

class ModelLoadError(AngelaError):
    """模型加载错误"""
    pass

class ConnectionError(AngelaError):
    """连接错误"""
    pass

def handle_errors(
    default_return=None,
    log_level: str = "ERROR",
    reraise: bool = False
):
    """
    统一错误处理装饰器

    Args:
        default_return: 出错时的默认返回值
        log_level: 日志级别
        reraise: 是否重新抛出异常
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AngelaError as e:
                getattr(logger, log_level.lower())(
                    f"[{func.__name__}] {e.code}: {e.message}",
                    extra={'details': e.details}
                )
                if reraise:
                    raise
                return default_return
            except (ValueError, KeyError, AttributeError) as e:
                getattr(logger, log_level.lower())(
                    f"[{func.__name__}] Expected error: {e}",
                    exc_info=True
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                getattr(logger, log_level.lower())(
                    f"[{func.__name__}] Unexpected error: {e}",
                    exc_info=True
                )
                if reraise:
                    raise
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AngelaError as e:
                getattr(logger, log_level.lower())(
                    f"[{func.__name__}] {e.code}: {e.message}",
                    extra={'details': e.details}
                )
                if reraise:
                    raise
                return default_return
            except (ValueError, KeyError, AttributeError) as e:
                getattr(logger, log_level.lower())(
                    f"[{func.__name__}] Expected error: {e}",
                    exc_info=True
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                getattr(logger, log_level.lower())(
                    f"[{func.__name__}] Unexpected error: {e}",
                    exc_info=True
                )
                if reraise:
                    raise
                return default_return

        # 根据函数类型返回相应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

# 使用示例
@handle_errors(default_return=None, reraise=True)
async def load_live2d_model(model_path: str):
    """加载 Live2D 模型"""
    if not os.path.exists(model_path):
        raise ModelLoadError(
            message=f"Model file not found: {model_path}",
            code="MODEL_NOT_FOUND",
            details={'path': model_path}
        )

    # ... 加载逻辑 ...
    return model
```

---

#### 任务组 3.2: 类型提示修复 (2个)

```
任务编号: P-MEDIUM-024 至 P-MEDIUM-025
优先级: P2 (中)
预计时间: 1-2 小时
依赖: 阶段 2 完成
```

**修复示例**:

```python
# apps/backend/src/core/shared/types/common_types.py

from typing import TypedDict, Literal, Optional
from datetime import datetime

# 修复前 (错误)
class ToolDispatcherResponse(TypedDict):
    status: Literal[]
    message: str

# 修复后
class ToolDispatcherResponse(TypedDict):
    status: Literal[
        "success",
        "failure_tool_not_found",
        "failure_tool_error",
        "failure_parsing_query",
        "error_dispatcher_issue",
        "unhandled_by_local_tool"
    ]
    message: str
    timestamp: float
    execution_time: float

# 使用示例
def dispatch_tool(tool_name: str, query: str) -> ToolDispatcherResponse:
    """分发工具任务"""
    start_time = time.time()

    try:
        result = execute_tool(tool_name, query)
        return ToolDispatcherResponse(
            status="success",
            message=f"Tool {tool_name} executed successfully",
            timestamp=datetime.now().timestamp(),
            execution_time=time.time() - start_time
        )
    except ValueError:
        return ToolDispatcherResponse(
            status="failure_tool_error",
            message=f"Tool {tool_name} execution failed",
            timestamp=datetime.now().timestamp(),
            execution_time=time.time() - start_time
        )
```

---

#### 任务组 3.3: 性能优化 (12个)

```
任务编号: P-MEDIUM-026 至 P-MEDIUM-037
优先级: P2 (中)
预计时间: 2-3 天
依赖: 阶段 2 完成
```

**修复示例: 任务池限制**

```python
# apps/backend/src/core/async/task_pool.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Coroutine
import logging

logger = logging.getLogger(__name__)

class TaskPool:
    """任务池管理器"""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
        self.max_workers = max_workers
        self.active_tasks = set()
        self.completed_tasks = 0

    async def run(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """运行任务"""
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            task_id = id(func)
            self.active_tasks.add(task_id)

            try:
                # 在线程池中执行同步函数
                if not asyncio.iscoroutinefunction(func):
                    result = await loop.run_in_executor(
                        self.executor,
                        lambda: func(*args, **kwargs)
                    )
                else:
                    # 直接运行异步函数
                    result = await func(*args, **kwargs)

                return result
            finally:
                self.active_tasks.discard(task_id)
                self.completed_tasks += 1

    async def run_batch(
        self,
        tasks: list[tuple[Callable, tuple, dict]]
    ) -> list[Any]:
        """批量运行任务"""
        return await asyncio.gather(*[
            self.run(func, *args, **kwargs)
            for func, args, kwargs in tasks
        ])

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'active_tasks': len(self.active_tasks),
            'completed_tasks': self.completed_tasks,
            'max_workers': self.max_workers
        }

    async def shutdown(self):
        """关闭任务池"""
        # 等待所有活动任务完成
        while self.active_tasks:
            await asyncio.sleep(0.1)

        self.executor.shutdown(wait=True)
        logger.info("Task pool shutdown complete")

# 使用示例
async def main():
    task_pool = TaskPool(max_workers=10)

    # 运行多个任务
    results = await task_pool.run_batch([
        (process_image, ('image1.jpg',), {}),
        (process_image, ('image2.jpg',), {}),
        (process_image, ('image3.jpg',), {}),
    ])

    print(f"Processed {len(results)} images")
    print(f"Stats: {task_pool.get_stats()}")

    await task_pool.shutdown()
```

---

### 🟢 阶段 4: LOW - 代码规范统一

**时间**: 2-4 周  
**依赖**: 阶段 3 完成  
**完成标准**: 代码风格统一，90%+ 测试覆盖率

#### 任务组 4.1: 代码风格统一

```
任务编号: P-LOW-001 至 P-LOW-050
优先级: P3 (低)
预计时间: 1-2 周
依赖: 阶段 3 完成
```

**配置文件**:

```yaml
# .pylintrc
[MASTER]
ignore=tests,venv,node_modules
max-line-length=120

[FORMAT]
indent-string='    '

[BASIC]
good-names=i,j,k,ex,Run,_

[DESIGN]
max-args=10
max-locals=15
max-returns=6
max-branches=12
max-statements=50
max-parents=7
max-attributes=7
min-public-methods=2
max-public-methods=20

[MESSAGES CONTROL]
disable=
    C0111,  # missing-docstring
    C0103,  # invalid-name
    R0903,  # too-few-public-methods
    R0913,  # too-many-arguments
    W0212,  # protected-access
```

```json
// .eslintrc.json
{
  "env": {
    "browser": true,
    "es2021": true,
    "node": true
  },
  "extends": ["eslint:recommended"],
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "rules": {
    "indent": ["error", 4],
    "linebreak-style": ["error", "unix"],
    "quotes": ["error", "single"],
    "semi": ["error", "always"],
    "no-unused-vars": "warn",
    "no-console": "warn",
    "max-len": ["warn", { "code": 120 }]
  }
}
```

---

#### 任务组 4.2: 日志系统实现

```
任务编号: J-LOW-001 至 J-LOW-020
优先级: P3 (低)
预计时间: 3-5 天
依赖: 阶段 3 完成
```

**实现示例**:

```javascript
// js/logger.js
/**
 * 统一日志系统
 */
class Logger {
  constructor(level = 'INFO') {
    this.level = level
    this.levels = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 }
    this.enabled = process.env.NODE_ENV !== 'production'
  }

  _shouldLog(level) {
    return this.enabled && this.levels[level] >= this.levels[this.level]
  }

  _formatMessage(level, message, data) {
    const timestamp = new Date().toISOString()
    const prefix = `[${timestamp}] [${level}]`
    const suffix = data ? ` ${JSON.stringify(data)}` : ''
    return `${prefix} ${message}${suffix}`
  }

  debug(message, data) {
    if (this._shouldLog('DEBUG')) {
      console.debug(this._formatMessage('DEBUG', message, data))
    }
  }

  info(message, data) {
    if (this._shouldLog('INFO')) {
      console.info(this._formatMessage('INFO', message, data))
    }
  }

  warn(message, data) {
    if (this._shouldLog('WARN')) {
      console.warn(this._formatMessage('WARN', message, data))
    }
  }

  error(message, data) {
    if (this._shouldLog('ERROR')) {
      console.error(this._formatMessage('ERROR', message, data))
    }
  }
}

// 导出单例
const logger = new Logger(process.env.LOG_LEVEL || 'INFO')

// 替换所有 console.log
// 使用: logger.info('Message', { key: value });
export default logger
```

---

### 🔴 阶段 5: 测试与验证 (持续)

**时间**: 贯穿整个修复过程  
**优先级**: P0 (最高)

#### 任务组 5.1: 单元测试

```bash
# 运行 Python 单元测试
pytest apps/backend/tests/ -v --tb=short --cov=apps/backend/src --cov-report=html

# 运行 JavaScript 单元测试
npm test
```

#### 任务组 5.2: 集成测试

```bash
# 综合功能测试
python3 comprehensive_test.py

# 端到端测试
python3 tests/integration/test_e2e.py
```

#### 任务组 5.3: 性能测试

```bash
# Live2D 性能测试
node tests/desktop-app/live2d_performance_test.js

# API 性能测试
python3 tests/api/performance_test.py

# 内存泄漏检测
python3 tests/memory/leak_detection.py
```

#### 任务组 5.4: 安全测试

```bash
# 安全扫描
bandit -r apps/backend/src/

# 依赖漏洞扫描
npm audit
pip-audit

# 路径遍历测试
python3 tests/security/path_traversal_test.py
```

---

## 📊 修复进度跟踪

| 阶段             | 任务数   | 已完成 | 进行中 | 待开始   | 完成率 | 状态      |
| ---------------- | -------- | ------ | ------ | -------- | ------ | --------- |
| 阶段 1: CRITICAL | 14       | 0      | 0      | 14       | 0%     | ⏳ 待开始 |
| 阶段 2: HIGH     | 199      | 0      | 0      | 199      | 0%     | ⏳ 待开始 |
| 阶段 3: MEDIUM   | 61       | 0      | 0      | 61       | 0%     | ⏳ 待开始 |
| 阶段 4: LOW      | 72+      | 0      | 0      | 72+      | 0%     | ⏳ 待开始 |
| 阶段 5: 测试     | 持续     | 0      | 0      | 持续     | 0%     | ⏳ 待开始 |
| **总计**         | **~350** | **0**  | **0**  | **~350** | **0%** | ⏳ 待开始 |

---

## 🎯 里程碑

### 里程碑 1: CRITICAL 修复完成

**时间**: 阶段 1 完成 (1-2小时)  
**标准**:

- ✅ 0 CRITICAL 错误
- ✅ 所有文件可正常导入
- ✅ 基础语法验证通过

### 里程碑 2: HIGH 修复完成

**时间**: 阶段 2 完成 (24-48小时)  
**标准**:

- ✅ 0 HIGH 级别安全问题
- ✅ 0 内存泄漏
- ✅ 所有导入错误已修复

### 里程碑 3: MEDIUM 修复完成

**时间**: 阶段 3 完成 (5-7天)  
**标准**:

- ✅ 0 裸异常捕获
- ✅ 所有类型提示正确
- ✅ 性能优化完成

### 里程碑 4: 代码规范完成

**时间**: 阶段 4 完成 (2-4周)  
**标准**:

- ✅ 代码风格统一
- ✅ 完整的日志系统
- ✅ 90%+ 测试覆盖率

### 里程碑 5: 生产就绪

**时间**: 阶段 5 完成 (持续)  
**标准**:

- ✅ 所有测试通过
- ✅ 性能指标达标
- ✅ 安全扫描通过
- ✅ 99.2% → 100%

---

## 🚀 立即行动

### 今天 (阶段 1)

1. **分配团队** (15 分钟)
   - Python 开发者: 1 人
   - JavaScript 开发者: 1 人
   - QA 工程师: 1 人

2. **开始修复** (1.5 小时)
   - 修复 12 个 Python 语法错误
   - 修复 2 个 JavaScript 语法错误
   - 运行验证脚本

3. **生成报告** (15 分钟)
   - 记录修复详情
   - 标记已解决的问题
   - 更新进度跟踪

### 本周 (阶段 2)

1. **第 1-2 天**: Python 导入错误修复
2. **第 3-4 天**: 安全问题修复
3. **第 5-6 天**: JavaScript 性能优化
4. **第 7 天**: 验证和测试

### 本月 (阶段 3-4)

1. **第 2 周**: 错误处理改进
2. **第 3 周**: 性能优化
3. **第 4 周**: 代码规范统一

---

**文档版本**: v1.0  
**创建日期**: 2026年2月10日  
**作者**: iFlow CLI  
**审核状态**: 待审核
