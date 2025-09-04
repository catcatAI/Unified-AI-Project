# Unified AI Project 1.0 部署指南

## 1. 系统要求

### 1.1 硬件要求
- **CPU**: Intel i5 或同等性能处理器
- **内存**: 16GB RAM (推荐32GB)
- **存储**: 50GB 可用磁盘空间
- **GPU**: 可选 (推荐NVIDIA GTX 1060或更高，用于GPU加速训练)

### 1.2 软件要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **Python**: 3.8 或更高版本
- **Node.js**: 16 或更高版本
- **Git**: 最新版本
- **Docker**: 可选 (用于容器化部署)

## 2. 环境准备

### 2.1 安装依赖
```bash
# 克隆项目仓库
git clone <repository-url>
cd unified-ai-project

# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖
npm install
```

### 2.2 配置环境变量
创建 `.env` 文件并配置必要的环境变量:
```env
# 数据库配置
DATABASE_URL=sqlite:///./data/database.db

# API密钥
OPENAI_API_KEY=your_openai_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key

# 其他配置
DEBUG=false
LOG_LEVEL=info
```

## 3. 服务启动

### 3.1 启动开发环境
```bash
# Windows
unified-ai.bat

# macOS/Linux
./unified-ai.sh
```

选择 "Start Development" -> "Start Full Development Environment"

### 3.2 启动生产环境
```bash
# 启动后端服务
cd apps/backend
python main.py

# 启动前端服务
cd frontend
npm start

# 启动桌面应用
cd desktop
npm start
```

## 4. 服务配置

### 4.1 后端配置
配置文件位于 `apps/backend/config/` 目录:
- `app_config.yaml`: 应用配置
- `database_config.yaml`: 数据库配置
- `security_config.yaml`: 安全配置

### 4.2 前端配置
配置文件位于 `frontend/config/` 目录:
- `app_config.json`: 应用配置
- `api_config.json`: API端点配置

### 4.3 桌面应用配置
配置文件位于 `desktop/config/` 目录:
- `app_config.json`: 应用配置
- `backend_config.json`: 后端连接配置

## 5. 数据库设置

### 5.1 初始化数据库
```bash
cd apps/backend
python scripts/init_database.py
```

### 5.2 数据库迁移
```bash
cd apps/backend
python scripts/migrate_database.py
```

## 6. 模型训练和部署

### 6.1 训练模型
```bash
# 使用CLI工具启动训练
unified-cli train start <model_name>

# 或直接运行训练脚本
cd training
python train_model.py --model <model_name>
```

### 6.2 部署模型
训练完成后，模型将自动部署到 `models/` 目录，可通过API访问。

## 7. 监控和日志

### 7.1 系统监控
访问 `http://localhost:8000/monitoring` 查看系统监控面板。

### 7.2 日志查看
日志文件位于 `logs/` 目录:
- `app.log`: 应用日志
- `error.log`: 错误日志
- `training.log`: 训练日志

## 8. 故障排除

### 8.1 常见问题

#### 问题1: 服务无法启动
**解决方案**:
1. 检查端口是否被占用
2. 确认所有依赖已正确安装
3. 检查环境变量配置

#### 问题2: GPU加速不工作
**解决方案**:
1. 确认已安装CUDA和cuDNN
2. 检查GPU驱动版本
3. 确认PyTorch或TensorFlow的GPU版本已安装

#### 问题3: 数据库连接失败
**解决方案**:
1. 检查数据库服务是否运行
2. 确认数据库配置正确
3. 检查防火墙设置

### 8.2 健康检查
运行健康检查脚本验证系统状态:
```bash
python scripts/health_check.py
```

## 9. 安全配置

### 9.1 API安全
- 启用HTTPS
- 配置API密钥验证
- 设置请求频率限制

### 9.2 数据安全
- 定期备份数据
- 启用数据加密
- 配置访问控制

## 10. 备份和恢复

### 10.1 自动备份
项目包含自动备份机制:
```bash
# 手动执行备份
tools/automated-backup.bat
```

### 10.2 数据恢复
```bash
# 从最新备份恢复
tools/enhanced-file-recovery.bat --latest

# 从特定备份恢复
tools/enhanced-file-recovery.bat --backup <backup_name>
```

## 11. 更新和维护

### 11.1 系统更新
```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt
npm install
```

### 11.2 定期维护任务
- 清理临时文件
- 优化数据库
- 更新模型

## 12. 支持和联系

如遇到问题，请联系项目维护团队或查看以下资源:
- 项目文档: [文档链接]
- GitHub Issues: [Issues链接]
- 技术支持邮箱: [support@unified-ai-project.org]

---
**注意**: 本部署指南基于Unified AI Project 1.0版本，如有更新，请参考最新文档。