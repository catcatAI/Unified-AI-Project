# Git 与项目结构管理指南

## 🎯 概述

本指南整合了项目中关于 Git 管理和项目结构的相关信息，旨在提供统一的项目维护和管理指导。

## 📁 项目结构分析

### 核心代码和配置 (应该版本控制的核心文件)
```
├── apps/                          # 核心应用模块
│   ├── backend/                   # Python AI后端服务
│   ├── desktop-app/               # Electron桌面应用  
│   └── frontend-dashboard/        # Web前端仪表板
├── packages/                      # 共享包和工具
│   ├── cli/                       # CLI工具
│   └── ui/                        # UI组件库
├── docs/                          # 项目文档
├── scripts/                       # 脚本工具
├── tests/                         # 测试框架
├── training/configs/              # 训练配置文件
├── package.json                   # Node.js配置
├── pnpm-workspace.yaml           # PNPM工作空间配置
├── eslint.config.mjs             # ESLint配置
└── .gitignore                     # Git忽略规则
```

### 小型示例和配置数据 (< 1MB)
```
data/
├── README.md                      # 数据说明文档 ✅
├── data_config.json              # 数据配置文件 ✅  
├── TRAINING_DATA_GUIDE.md        # 训练数据指南 ✅
├── audio_samples/                 # 小型音频示例 ✅
├── vision_samples/                # 小型视觉示例 ✅
├── reasoning_samples/             # 推理示例 ✅
└── multimodal_samples/           # 多模态示例 ✅
```

### 大型数据文件 (已添加到.gitignore)
#### 训练数据集 (~76GB总计)
```
data/
├── common_voice_zh/              # 57.05GB - Common Voice中文语音数据
│   ├── zh-CN/                    # 中文大陆数据集
│   ├── zh-TW/                    # 中文台湾数据集  
│   ├── singleword/               # 单字数据集
│   └── *.tar.gz                  # 原始压缩档案
├── visual_genome_sample/         # 18.2GB - Visual Genome场景理解
├── coco_captions/                # 1.01GB - MS COCO图像描述
└── flickr30k_sample/            # 0.05GB - Flickr30K视觉-语言理解
```

#### 缓存和临时数据
```
data/
├── atlassian_cache/              # Atlassian缓存文件
├── fallback_comm/                # 通信回退数据
├── task_queue/                   # 任务队列数据
└── demo_learning/                # 演示学习数据
```

#### 训练产出文件
```
data/
├── checkpoints/                  # 训练检查点 (ED3N: ed3n_full.json; GARDEN: garden_checkpoint/)
└── state/                        # 运行时状态 (TrainingCoordinator 等)
```

## 🛠️ Git 管理策略

### .gitignore 更新内容
已添加以下规则到.gitignore：

```gitignore
# Large Training Datasets (should not be committed to Git)
data/common_voice_zh/              # 57GB Common Voice Chinese datasets
data/visual_genome_sample/         # 18GB Visual Genome dataset  
data/coco_captions/                # 1GB MS COCO captions
data/flickr30k_sample/             # Flickr30K sample data

# Training artifacts and model files
data/checkpoints/                  # Training checkpoints (ED3N ed3n_full.json, GARDEN garden_checkpoint/)
data/state/                        # Runtime training state
*.tar.gz                          # Compressed dataset archives
*.zip                             # Dataset archives

# Data processing artifacts  
data/processed_data/              # Processed data
data/temp_data/                   # Temporary data
data/atlassian_cache/             # Cache files
data/fallback_comm/               # Communication fallback data
data/task_queue/                  # Temporary task data
```

### 文件分类策略

#### 🟢 应该提交的文件 (项目本体)
- **批处理脚本**: 所有 *.bat 文件 (包括新的 unified-ai.bat)
- **核心组件**: apps/backend/diagnose_components.py
- **文档**: 所有 *.md 文件
- **配置**: .gitignore, package.json 等
- **小型示例数据**: README 和配置文件

#### 🔴 不应该追踪的文件 (大型数据)
- **Common Voice数据**: 57GB中文语音数据
- **Visual Genome数据**: 18GB视觉数据
- **MS COCO数据**: 1GB图像描述数据
- **临时文件**: 测试报告、快取文件

#### 🟡 需要清理的文件 (临时)
- **测试报告**: agi_integration_test_report_*.txt
- **压缩档案**: master.zip, annotations.zip
- **快取目录**: 各种临时处理文件

## 🔧 可用工具

### unified-ai.bat - 统一管理工具 (推荐)
**用途**: 统一管理项目的各种功能
**特点**:
- ✅ 整合所有常用功能
- ✅ 简化操作流程
- ✅ 提供友好的菜单界面
- ✅ 包含所有原有脚本的功能

**使用方法**:
```cmd
双击运行 unified-ai.bat
```

### safe-git-cleanup.bat - 安全Git状态清理工具
**用途**: 安全地清理Git状态
**特点**:
- ✅ 只添加重要的项目文件
- 🛡️ 不会删除任何现有文件
- 📋 确保.gitignore正确忽略临时文件
- 🚀 安全提交和推送

**使用方法**:
```cmd
双击运行 safe-git-cleanup.bat
```

### Git状态检查流程
1. 运行 `git status` 检查当前状态
2. 确认大型数据集不在追踪列表中
3. 确认核心文件已正确添加
4. 运行安全清理脚本提交重要更改

## 📊 存储空间分析

| 类别 | 大小 | 描述 | Git管理 |
|------|------|------|---------|
| 项目核心代码 | ~50MB | 应用代码、配置、文档 | ✅ 是 |
| 小型示例数据 | ~1MB | 演示和配置数据 | ✅ 是 |
| **Common Voice** | **57.05GB** | 中文语音训练数据 | ❌ 否 |
| **Visual Genome** | **18.2GB** | 视觉场景理解数据 | ❌ 否 |
| **MS COCO** | **1.01GB** | 图像描述数据 | ❌ 否 |
| 其他数据集 | ~0.05GB | Flickr30K等 | ❌ 否 |

## 🎯 建议的工作流程

### 代码开发
- 修改核心代码时正常使用Git版本控制
- 小型配置和示例数据可以提交
- 文档更新应该及时提交

### 数据管理  
- 大型数据集本地管理，不提交到Git
- 使用脚本工具自动下载和管理数据集
- 在README中记录数据获取方式

### 训练模型
- 训练产出的模型文件不提交到Git
- 重要的训练配置和脚本需要版本控制
- 训练日志可以选择性保留重要结果

## 🔒 安全机制说明

### 自动备份
- 安全清理脚本会创建备份分支
- 保护重要文件不被误删

### 分支检测
- 自动检测当前分支
- 推送到正确的远程分支
- 避免意外推送到main分支

### 预检查机制
- Git仓库有效性检查
- 未提交变更警告
- 用户确认机制

## ⚠️ 重要注意事项

### 执行前务必确认
1. **当前目录**: 确保在项目根目录执行
2. **备份重要数据**: 虽然脚本有自动备份，但重要数据最好另外备份
3. **网络连接**: 推送操作需要稳定的网络连接
4. **权限确认**: 确保有仓库的推送权限

### 大型数据集管理
项目包含以下大型数据集（~76GB），这些**不应该**被Git追踪：
- `data/common_voice_zh/` (57GB) - Common Voice中文数据
- `data/visual_genome_sample/` (18GB) - Visual Genome数据
- `data/coco_captions/` (1GB) - MS COCO图像描述
- `data/flickr30k_sample/` (50MB) - Flickr30K数据

### 应该被Git追踪的文件
- 核心代码 (`apps/`, `packages/`)
- 配置文件 (`.gitignore`, `package.json`, 等)
- 文档 (`*.md`)
- 脚本 (`*.bat`, `scripts/`)
- 小型示例数据 (< 1MB)

## 🚨 故障排除

### 如果脚本执行失败
1. **检查错误信息**: 仔细阅读输出的错误信息
2. **恢复备份**: `git checkout 备份分支名`
3. **手动修复**: 根据错误信息进行手动操作
4. **重新检查**: 运行 `git status`

### 如果推送失败
1. **检查网络**: 确保网络连接正常
2. **检查权限**: 确保有仓库推送权限
3. **检查分支**: 确认推送到正确的分支
4. **手动推送**: `git push origin 分支名`

### 如果数据丢失
1. **检查备份分支**: `git branch -a`
2. **恢复备份**: `git checkout 备份分支名`
3. **检查工作目录**: 确认文件是否在工作目录中
4. **联系支援**: 如果问题持续存在

## ✅ 当前状态确认

- **项目结构**: 清晰分离代码和数据 ✅
- **Git配置**: 正确忽略大型文件 ✅  
- **数据完整性**: Common Voice等数据集完整 ✅
- **脚本工具**: 数据下载和管理工具完善 ✅

## 📚 相关文档

- 数据使用指南: `data/TRAINING_DATA_GUIDE.md`
- 训练设置指南: `TRAINING_SETUP_GUIDE.md`  
- Common Voice处理报告: `COMMON_VOICE_PROCESSING_REPORT.md`

---
**最后更新**: 2025年8月24日  
**数据总量**: ~76GB训练数据 + ~50MB项目代码  
**状态**: 项目结构优化完成，可以安全进行版本控制