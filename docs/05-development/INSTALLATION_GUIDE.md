# Angela AI 安装指南

## Installation Guide

---

## 🚀 快速开始（推荐）

### 一键安装（新用户推荐）

> ⚠️ **2026-10 更正**：本節原本指示下載獨立的
> `install_angela.py`。該檔案已從專案移除，功能整併進專案根目錄的
> `setup.py`，GitHub 上已不存在 `install_angela.py`，原本的 `curl`
> 連結會 404。請改用下方流程。

**最簡單的方式** — 取得專案檔案後，執行內建安裝程式：

#### Windows:

1. **取得專案檔案**

   ```powershell
   # 打开PowerShell或CMD，运行：
   git clone https://github.com/catcatAI/Unified-AI-Project.git
   cd Unified-AI-Project
   ```

2. **运行安装**

   ```powershell
   python setup.py
   ```

   或双击专案资料夹中的 `setup.py` 文件

3. **按提示操作**
   - 选择安装目录（默认：当前目录；可用 `--install-dir` 指定）
   - 等待依赖安装（5-10分钟；可用 `--skip-deps` 跳过）
   - 建立桌面／开始菜单捷径（可用 `--skip-shortcuts` 跳过）
   - 完成！

4. **启动Angela**
   - 双击桌面快捷方式 **"Angela AI"**
   - 或从开始菜单启动

---

#### macOS/Linux:

```bash
# 取得專案檔案
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 运行安装
python3 setup.py

# 启动
python scripts/run_angela.py
```

---

## 💻 开发者安装

### 手动安装（适合想修改代码的开发者）

```bash
# 1. 克隆仓库
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 2. 创建虚拟环境（推荐，避免污染系统 Python）
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. 安装依赖（分层，按需选择）
pip install -e ./apps/backend                    # 轻量 BASE：可启动服务器 + 核心 AI（纯 numpy 后端）
pip install -e "./apps/backend[standard]"        # 完整功能层（推荐用户）：+ torch/ml、向量库、STT 等
pip install -e "./apps/backend[dev]"             # 贡献者：standard + pytest/lint/typecheck 工具链
# 或者等价的一键方式：
# pip install -r requirements.txt

# 4. 一键初始化（硬件检测 → 下载数据集 → 训练模型 → 验证；--skip-download / --skip-training 可跳过）
python setup.py

# 5. 启动
python scripts/run_angela.py
```

#### 功能组 extras 一览（`pip install -e "./apps/backend[<组名>]"`）

| 组名      | 内容                                         | 适用场景                                          |
| --------- | -------------------------------------------- | ------------------------------------------------- |
| `ml`      | torch / transformers / sentence-transformers | 神经嵌入、SNN torch 后端                          |
| `vector`  | chromadb                                     | 持久化向量库（无则回退 numpy+JSON）               |
| `data`    | pandas / scikit-learn / textblob             | 表格分析、情感分析                                |
| `media`   | pyautogui / pytesseract / pywebview          | 屏幕控制、OCR、桌面窗口                           |
| `audio`   | SpeechRecognition / faster-whisper           | 语音识别 STT                                      |
| `gpu`     | pynvml                                       | NVIDIA GPU 遥测                                   |
| `cache`   | redis                                        | Redis 缓存后端                                    |
| `google`  | Google API 客户端套件                        | Drive / Gmail 集成                                |
| `docs`    | beautifulsoup4 / python-docx / openpyxl      | 文档处理                                          |
| `tracing` | OpenTelemetry                                | 分布式追踪（可选观测性）                          |
| `browser` | playwright                                   | 无头浏览器自动化（需再执行 `playwright install`） |

> 💡
> **低内存设备提示**：torch 默认从 PyPI 安装的是捆绑 CUDA 的版本（约 2GB+）。若无需 GPU 或内存有限，建议先装 CPU 版：
>
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -e "./apps/backend[ml]"
> ```

---

## 🐳 Docker安装

```bash
# 克隆仓库
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 启动Docker容器
docker-compose up -d
```

---

## 📋 安装选项对比

| 方式         | 适用对象 | 难度        | 特点                                    |
| ------------ | -------- | ----------- | --------------------------------------- |
| **一键安装** | 新用户   | ⭐ 最简单   | 自动安装依赖、建立桌面/开始菜单快捷方式 |
| **手动安装** | 开发者   | ⭐⭐ 中等   | 可修改代码、灵活配置                    |
| **Docker**   | 高级用户 | ⭐⭐⭐ 复杂 | 容器化部署、隔离环境                    |

---

## 🔧 安装程序详解

### setup.py 功能（`install_angela.py` 的后继者）

**这个安装程序会：**

1. **系统检查**
   - ✅ Python 3.10+ 版本检查
   - ✅ 磁盘空间检查（需要2GB+）

2. **依赖安装**
   - 📦 安装 `apps/backend` 的依赖
   - 🎵 安装音频支持（pyaudio等）
   - ⏱️ 耗时：5-10分钟（取决于网络）

3. **快捷方式**
   - 🖥️ 创建桌面快捷方式（仅 Windows）
   - 📋 创建开始菜单项（仅 Windows）

4. **完成提示**
   - 📖 显示安装摘要
   - 🚀 说明启动方式
   - 💡 提供首次使用提示

> ℹ️ 与旧版 `install_angela.py`
> 的差异：不再自行从 GitHub 克隆代码（请先 clone 本专案），因此没有 `--repo` /
> `--skip-clone` 选项；也不再产生卸载程序。

---

## ⚙️ 高级选项

### 自定义安装目录

```bash
# 安装到D盘
python setup.py --install-dir "D:\AngelaAI"

# 安装到任意位置
python setup.py --install-dir "/path/to/install"
```

### 使用其他仓库（fork）

先用 `git clone` 取得该 fork，再在资料夹内执行安装程式：

```bash
# 安装fork的版本
git clone https://github.com/yourname/Unified-AI-Project.git
cd Unified-AI-Project
python setup.py
```

### 跳过某些步骤

```bash
# 跳过依赖安装（只创建快捷方式）
python setup.py --skip-deps

# 跳过快捷方式创建
python setup.py --skip-shortcuts
```

---

## 🗑️ 卸载

> ⚠️ **2026-10 更正**：旧版 `install_angela.py` 会产生卸载程序，且文件名为
> `uninstall.py`。两者都已从专案移除，目前**没有**内建卸载程式，请手动删除安装目录。

### 手动删除

删除当初指定的安装目录（预设为 clone 下来的专案资料夹，例如 `~/AngelaAI` 或
`%USERPROFILE%\AngelaAI`）：

```bash
# Windows
rmdir /s /q "%USERPROFILE%\AngelaAI"

# macOS/Linux
rm -rf ~/AngelaAI
```

若安装时建立了桌面／开始菜单捷径，也请一并手动删除。

---

## ❓ 常见问题

### Q: 安装失败，提示"Git未安装"

**A:** 安装程式本身不再代为下载 git。请先安装 Git（https://git-scm.com），或从
GitHub 网页版下载 ZIP 解压缩后再执行 `python setup.py`。

### Q: 依赖安装超时

**A:** 网络问题，可以：

1. 更换pip源：`pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`
2. 使用代理
3. 手动安装：`pip install -r requirements.txt --user`

### Q: 如何更新到最新版本？

**A:**

```bash
cd ~/AngelaAI     # 你的安装/克隆目录
git pull origin main
pip install -e "apps/backend"          # 或 apps/backend[standard]，与首次安装时相同层级
npx pnpm install --no-frozen-lockfile
```

### Q: 安装后找不到快捷方式

**A:** 可以手动创建快捷方式指向：`python scripts/run_angela.py`

### Q: 提示缺少XXX.dll

**A:** Windows需要安装Visual C++
Redistributable，下载：https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📊 系统要求

### 最低配置

- **Python**: 3.10+
- **RAM**: 4GB
- **磁盘**: 2GB 可用空间
- **系统**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

### 推荐配置

- **Python**: 3.11 或 3.12
- **RAM**: 8GB+
- **磁盘**: 5GB+ 可用空间
- **GPU**: 支持CUDA的NVIDIA显卡（加速AI推理）

---

## 🎉 安装完成后

### 首次启动

1. **配置API密钥**（可选，用于文件管理功能）

   ```bash
   # 复制示例配置文件
   cp apps/backend/config/credentials.example.json ~/.config/angela-ai/credentials.json

   # 编辑填入你的Google API密钥
   nano ~/.config/angela-ai/credentials.json
   ```

2. **启动Angela**

   ```bash
   # 方法1：双击桌面快捷方式
   # 方法2：终端运行（在你的项目/安装目录）
   python scripts/run_angela.py
   ```

3. **等待初始化**
   - 加载生物系统
   - 初始化Live2D模型
   - 显示在桌面

---

## 📚 相关文档

- **使用指南**: [README.md](../../README.md)
- **项目概览**: [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)
- **模组地图**: [MODULE_MAP.md](../MODULE_MAP.md)
- **艺术学习**:
  [ART_LEARNING_LIVE2D_GUIDE.md](../04-advanced-concepts/ART_LEARNING_LIVE2D_GUIDE.md)
- **API文档**:
  [docs/03-technical-architecture/api/](../03-technical-architecture/api/)

---

## 💬 需要帮助？

- **GitHub Issues**: https://github.com/catcatAI/Unified-AI-Project/issues
- **Discussions**: https://github.com/catcatAI/Unified-AI-Project/discussions
- **Email**: support@catcatai.com

---

**安装完成后，Angela会在你的桌面上"活"起来！** 🎊

---

_更新日期_: 2026-02-02 _作者_: CatCatAI Development Team
