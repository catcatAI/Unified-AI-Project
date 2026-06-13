# Angela AI 安装指南
## Installation Guide

---

## 🚀 快速开始（推荐）

### 一键安装（新用户推荐）

**最简单的方式** - 只需下载一个文件，运行即可：

#### Windows:
1. **下载安装程序**
   ```powershell
   # 打开PowerShell或CMD，运行：
   curl -o install_angela.py https://raw.githubusercontent.com/catcatAI/Unified-AI-Project/main/install_angela.py
   ```

2. **运行安装**
   ```powershell
   python install_angela.py
   ```
   或双击下载的 `install_angela.py` 文件

3. **按提示操作**
   - 选择安装目录（默认：`C:\Users\你的用户名\AngelaAI`）
   - 等待自动从GitHub拉取代码
   - 等待依赖安装（5-10分钟）
   - 完成！

4. **启动Angela**
   - 双击桌面快捷方式 **"Angela AI"**
   - 或从开始菜单启动

---

#### macOS/Linux:
```bash
# 下载安装程序
curl -o install_angela.py https://raw.githubusercontent.com/catcatAI/Unified-AI-Project/main/install_angela.py

# 运行安装
python3 install_angela.py

# 启动
cd ~/AngelaAI
python scripts/run_angela.py
```

---

## 💻 开发者安装

### 手动安装（适合想修改代码的开发者）

```bash
# 1. 克隆仓库
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# 2. 安装依赖
pip install -r requirements.txt --user

# 3. 创建快捷方式
python setup.py

# 4. 启动
python scripts/run_angela.py
```

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

| 方式 | 适用对象 | 难度 | 特点 |
|------|----------|------|------|
| **一键安装** | 新用户 | ⭐ 最简单 | 自动下载、自动安装、创建快捷方式 |
| **手动安装** | 开发者 | ⭐⭐ 中等 | 可修改代码、灵活配置 |
| **Docker** | 高级用户 | ⭐⭐⭐ 复杂 | 容器化部署、隔离环境 |

---

## 🔧 安装程序详解

### install_angela.py 功能

**这个安装程序会：**

1. **系统检查**
   - ✅ Python 3.9+ 版本检查
   - ✅ pip 包管理器检查
   - ✅ Git 版本控制检查
   - ✅ 磁盘空间检查（需要2GB+）

2. **代码获取**
   - 📥 从GitHub克隆最新代码
   - 🔄 如果Git不可用，自动下载ZIP
   - 📂 安装到指定目录（默认用户目录）

3. **依赖安装**
   - 📦 安装 requirements.txt 中的所有依赖
   - 🎵 安装音频支持（pyaudio等）
   - ⏱️ 耗时：5-10分钟（取决于网络）

4. **快捷方式**
   - 🖥️ 创建桌面快捷方式
   - 📋 创建开始菜单项
   - 🗑️ 创建卸载程序

5. **完成提示**
   - 📖 显示安装摘要
   - 🚀 说明启动方式
   - 💡 提供首次使用提示

---

## ⚙️ 高级选项

### 自定义安装目录

```bash
# 安装到D盘
python install_angela.py --install-dir "D:\AngelaAI"

# 安装到任意位置
python install_angela.py --install-dir "/path/to/install"
```

### 使用其他仓库

```bash
# 安装fork的版本
python install_angela.py --repo https://github.com/yourname/Unified-AI-Project.git
```

### 跳过某些步骤

```bash
# 跳过克隆（如果已在项目目录）
python install_angela.py --skip-clone

# 跳过依赖安装
python install_angela.py --skip-deps

# 跳过快捷方式创建
python install_angela.py --skip-shortcuts
```

---

## 🗑️ 卸载

### 方法一：使用卸载程序（推荐）

**Windows:**
- 开始菜单 → Angela AI → 卸载 Angela AI
- 或在安装目录运行：`python uninstall.py`

**macOS/Linux:**
```bash
cd ~/AngelaAI
python uninstall.py
```

### 方法二：手动删除

```bash
# Windows
rmdir /s /q "%USERPROFILE%\AngelaAI"

# macOS/Linux
rm -rf ~/AngelaAI
```

---

## ❓ 常见问题

### Q: 安装失败，提示"Git未安装"
**A:** 安装程序会自动尝试下载ZIP文件作为备选。也可以手动安装Git：https://git-scm.com

### Q: 依赖安装超时
**A:** 网络问题，可以：
1. 更换pip源：`pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`
2. 使用代理
3. 手动安装：`pip install -r requirements.txt --user`

### Q: 如何更新到最新版本？
**A:** 
```bash
cd ~/AngelaAI
git pull origin main
pip install -r requirements.txt --upgrade
```

### Q: 安装后找不到快捷方式
**A:** 可以手动创建快捷方式指向：`python scripts/run_angela.py`

### Q: 提示缺少XXX.dll
**A:** Windows需要安装Visual C++ Redistributable，下载：https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📊 系统要求

### 最低配置
- **Python**: 3.9+
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
   # 方法2：终端运行
   cd ~/AngelaAI
   python scripts/run_angela.py
   ```

3. **等待初始化**
   - 加载生物系统
   - 初始化Live2D模型
   - 显示在桌面

---

## 📚 相关文档

- **使用指南**: [README.md](../README.md)
- **项目结构**: [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
- **艺术学习**: [docs/ART_LEARNING_LIVE2D_GUIDE.md](ART_LEARNING_LIVE2D_GUIDE.md)
- **API文档**: [docs/02-api-docs/](02-api-docs/)

---

## 💬 需要帮助？

- **GitHub Issues**: https://github.com/catcatAI/Unified-AI-Project/issues
- **Discussions**: https://github.com/catcatAI/Unified-AI-Project/discussions
- **Email**: support@catcatai.com

---

**安装完成后，Angela会在你的桌面上"活"起来！** 🎊

---

*文档版本*: v6.0.0  
*更新日期*: 2026-02-02  
*作者*: CatCatAI Development Team
