# Unified AI Project 配置与设置指南

本指南详细说明了Unified AI Project项目的配置和设置要求，包括自动生成和手动编辑的部分。

## 项目概述

Unified AI Project是一个基于monorepo的综合性AI系统项目，采用Python后端和多种前端技术构建。项目包含多个子系统和组件，需要正确的配置才能正常运行。

## 项目结构概览

```
Unified-AI-Project/
├── apps/
│   ├── backend/              # Python后端核心代码
│   ├── frontend-dashboard/   # Web前端仪表板
│   └── desktop-app/          # Electron桌面应用
├── packages/                 # 共享包
├── training/                 # 训练系统相关文件
├── docs/                     # 文档
├── scripts/                  # 脚本文件
└── tools/                    # 工具文件
```

## 自动化配置部分

以下配置可以通过脚本自动生成或由包管理器自动处理：

### 1. 依赖管理

#### Python依赖
- **主依赖**: `requirements.txt` - 项目运行所需的核心依赖
- **开发依赖**: `requirements-dev.txt` - 开发和测试所需的额外依赖
- **可选依赖**: `pyproject.toml` 中定义的可选依赖组（minimal, standard, full等）

#### Node.js依赖
- **工作区依赖**: `package.json` 中定义的根级依赖
- **应用依赖**: 各个应用目录下的 `package.json` 文件

### 2. 构建配置

#### Python构建
- `pyproject.toml` - 包含构建系统配置、项目元数据和工具配置
- `setup.py` - 传统的Python包设置文件

#### Node.js构建
- `pnpm-workspace.yaml` - 定义monorepo工作区
- 各应用的构建配置（如Vite, Webpack等）

### 3. 开发工具配置

#### 代码格式化
- `tool.black` - Black代码格式化工具配置
- `tool.isort` - import语句排序工具配置

#### 类型检查
- `tool.mypy` - MyPy类型检查工具配置

#### 代码质量
- `tool.pylint` - Pylint代码质量检查配置
- `tool.bandit` - 安全检查工具配置

### 4. 测试配置

#### Pytest配置
- `pytest.ini` - Pytest测试框架配置
- `tool.pytest.ini_options` - pyproject.toml中的Pytest配置

#### 测试脚本
- `apps/backend/scripts/workflow_controller.py` - 测试工作流控制器
- `apps/backend/scripts/auto_fix_complete.py` - 自动修复脚本

## 手动配置部分

以下配置需要手动编辑和设置：

### 1. 环境变量配置

#### .env文件
需要在以下位置创建和配置环境变量文件：
- `apps/backend/.env` - 后端环境变量
- `apps/frontend-dashboard/.env` - 前端环境变量

关键环境变量包括：
- 数据库连接信息
- API密钥和认证信息
- 服务端点配置
- 调试和日志配置

#### 示例配置
```env
# 数据库配置
DATABASE_URL=sqlite:///./test.db

# API密钥
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# 服务配置
BACKEND_HOST=localhost
BACKEND_PORT=8000

# 调试配置
DEBUG=true
LOG_LEVEL=INFO
```

### 2. 配置文件

#### YAML配置文件
- `apps/backend/configs/prompts.yaml` - LLM提示模板配置
- `apps/backend/configs/system_config.yaml` - 系统配置文件

#### JSON配置文件
- `apps/backend/configs/model_config.json` - 模型配置文件
- `apps/backend/configs/training_config.json` - 训练配置文件

### 3. 数据库设置

#### 数据库初始化
需要手动执行数据库迁移和初始化脚本：
```bash
cd apps/backend
python scripts/init_database.py
```

#### 数据库连接配置
在环境变量中设置正确的数据库连接字符串。

### 4. 服务配置

#### HSP协议配置
需要配置HSP连接器的相关参数：
- MQTT服务器地址和端口
- 认证信息
- 主题配置

#### 外部服务集成
- Atlassian集成配置（Confluence, Jira）
- 第三方API密钥配置
- 云服务配置（如Firebase）

## 启动服务

### 方法一：一键启动（推荐）

在项目根目录下执行：

```bash
pnpm dev
```

这将同时启动后端API服务（端口8000）和前端仪表板（端口3000）。

### 方法二：分别启动服务

#### 启动后端服务

```bash
pnpm dev:backend
```

或者直接使用Python：

```bash
cd apps/backend
python -m uvicorn src.services.main_api_server:app --host 127.0.0.1 --port 8000
```

#### 启动前端服务

```bash
pnpm dev:dashboard
```

## 访问应用

启动成功后，您可以访问以下地址：

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 常见问题

### 1. 端口被占用

如果提示端口被占用，可以使用以下命令杀死占用端口的进程：

```bash
# 杀死占用8000端口的进程（后端）
node scripts/port_manager.js kill-service BACKEND_API

# 杀死占用3000端口的进程（前端）
node scripts/port_manager.js kill-service FRONTEND_DASHBOARD
```

### 2. 服务无法启动

如果服务无法启动，请检查：

1. 确保所有依赖已正确安装
2. 检查是否有导入错误
3. 确认端口未被其他程序占用
4. 查看控制台输出的错误信息

## 安装和设置步骤

### 1. 环境准备

#### Python环境
```bash
# 创建虚拟环境
cd apps/backend
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（Linux/Mac）
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Node.js环境
```bash
# 安装pnpm（如果尚未安装）
npm install -g pnpm

# 安装项目依赖
pnpm install
```

### 2. 配置文件设置

#### 创建环境变量文件
```bash
# 在apps/backend目录下创建.env文件
cp .env.example .env
# 编辑.env文件，填入实际配置
```

#### 配置YAML文件
检查并根据需要修改以下文件：
- `apps/backend/configs/prompts.yaml`
- `apps/backend/configs/system_config.yaml`

### 3. 数据库初始化

```bash
cd apps/backend
python scripts/init_database.py
```

### 4. 模型下载和设置

某些AI模型需要手动下载或通过脚本下载：
```bash
cd apps/backend
python scripts/download_models.py
```

## 启动和运行

### 后端服务
```bash
cd apps/backend
# 开发模式
pnpm dev:api

# 或使用Python直接运行
python -m uvicorn src.services.main_api_server:app --reload --host 127.0.0.1 --port 8000
```

### 前端仪表板
```bash
# 启动前端开发服务器
pnpm dev:dashboard
```

### 桌面应用
```bash
# 启动桌面应用
pnpm dev:desktop
```

### 完整开发环境
```bash
# 同时启动后端和前端
pnpm dev

# 启动所有服务（包括桌面应用）
pnpm dev:all
```

## 测试运行

### 运行所有测试
```bash
pnpm test
```

### 运行后端测试
```bash
cd apps/backend
python scripts/workflow_controller.py
```

### 运行特定测试
```bash
cd apps/backend
python -m pytest tests/specific_test_file.py -v
```

## 故障排除

### 常见问题

1. **依赖安装失败**
   - 确保使用正确的Python版本（>=3.8）
   - 检查网络连接
   - 尝试使用国内镜像源

2. **环境变量未生效**
   - 确认.env文件位置正确
   - 检查变量名称是否正确
   - 重启开发服务器

3. **数据库连接失败**
   - 检查数据库服务是否运行
   - 验证连接字符串配置
   - 确认数据库权限设置

4. **模型加载失败**
   - 检查模型文件是否存在
   - 验证模型路径配置
   - 确认磁盘空间充足

### 日志查看

#### 后端日志
```bash
# 查看后端日志
tail -f apps/backend/logs/backend.log
```

#### 前端日志
前端日志通常在浏览器开发者工具中查看。

## 维护和更新

### 依赖更新
```bash
# 更新Python依赖
cd apps/backend
pip install --upgrade -r requirements.txt

# 更新Node.js依赖
pnpm update
```

### 配置备份
建议定期备份以下配置文件：
- 所有.env文件
- YAML和JSON配置文件
- 数据库文件（如果使用文件数据库）

## 安全注意事项

1. **API密钥保护**
   - 不要在代码中硬编码API密钥
   - 使用环境变量存储敏感信息
   - 定期轮换API密钥

2. **数据库安全**
   - 使用强密码
   - 限制数据库访问权限
   - 定期备份数据

3. **网络安全**
   - 使用HTTPS
   - 验证用户输入
   - 实施适当的认证和授权机制

## 总结

本指南涵盖了Unified AI Project项目的主要配置和设置要求。自动化部分可以通过脚本和包管理器处理，而手动配置部分需要根据具体环境和需求进行设置。正确配置项目是确保系统正常运行的关键步骤。