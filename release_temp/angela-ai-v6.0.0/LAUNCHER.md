## ✅ 后端核心逻辑验证指南 (推荐)

此脚本 `launcher.py` 旨在在隔离环境中验证 `Unified AI Project` 后端的核心逻辑、`SystemManager` 及其所有核心组件的初始化和关闭流程。它不涉及 `uvicorn` 环境，因此可以稳定运行并**成功验证所有后端功能**，包括新集成的 AGI 学习迴路。

**运行此脚本的先决条件：**
1.  **激活 Python 虚拟环境**：确保所有依赖项都已正确安装到虚拟环境中。
2.  **清除 `__pycache__`**：确保 `apps/backend/src` 目录及其子目录中没有残留的 `__pycache__` 文件夹。

```bash
# 在项目根目录下执行
python launcher.py
```

---

## ⚠️ 完整系统启动 (架构挑战)

以下是通常用于启动完整系统的命令，但**目前仍存在架构层面的冲突**，可能导致应用静默崩溃，无法提供完整的 API 功能。此问题已识别为「维度的不匹配」，需要架构级别的解决方案。

```bash
# 在项目根目录下执行
pnpm dev
```

### 🖥️ Frontend Dashboard (受限功能)
**[http://localhost:3000](http://localhost:3000)**
*由于后端API无法稳定启动，前端界面当前可能无法完全工作。*

### ⚙️ Backend API (不可用)
**[http://localhost:8000/docs](http://localhost:8000/docs)**
*由于后端API无法稳定启动，API 文档当前无法访问。*

