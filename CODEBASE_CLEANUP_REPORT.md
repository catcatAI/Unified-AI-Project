# Angela AI 代码库清理报告

## 📊 问题汇总

### 1. 废弃文件（建议删除）

| 文件 | 大小 | 原因 |
|------|------|------|
| `apps/backend/src/ai/reasoning/causal_reasoning_engine_backup_*.py` | 14KB | 备份文件 |
| `apps/backend/src/ai/reasoning/causal_reasoning_engine_before_integration_*.py` | 15KB | 旧版本 |
| `apps/backend/backup/integration_fix_*` | - | 旧集成修复 |
| `apps/backend/context_storage/*.json` | 101MB | 临时上下文 |

### 2. 重复文件（建议合并）

| 文件1 | 文件2 | 建议 |
|-------|-------|------|
| `ai/concept_models/causal_reasoning_engine.py` (37KB) | `ai/reasoning/real_causal_reasoning_engine.py` (47KB) | 保留 reasoning/ 版本 |
| `core/demo_feedback_loop.py` | `core/feedback_loop_engine.py` | 保留 feedback_loop_engine.py |

### 3. 命名不一致

| 当前名称 | 建议名称 |
|---------|---------|
| `angela_desktop_demo.py` | `desktop_demo.py` |
| `angela_real_creator.py` | `real_creator.py` |
| `real_comfyui_api.py` | `comfyui_api.py` |
| `real_edge_tts.py` | `edge_tts.py` |
| `real_playwright_browser.py` | `playwright_browser.py` |

---

## 🎯 清理计划

### Phase 1: 删除废弃文件
- [ ] 删除 causal_reasoning_engine_backup_*.py
- [ ] 删除 causal_reasoning_engine_before_integration_*.py
- [ ] 清空 context_storage/ 目录（或移动到 logs/）
- [ ] 删除 backup/integration_fix_* 目录

### Phase 2: 统一命名
- [ ] 重命名 art/ 目录下的 angela_* 文件
- [ ] 创建统一的 exports.py

### Phase 3: 合并重复代码
- [ ] 分析并合并 causal_reasoning 相关文件
- [ ] 分析并合并 feedback 相关文件

### Phase 4: 优化文件结构
- [ ] 确保 core/ 和 ai/ 目录分工明确
- [ ] 更新 imports

---

## 执行时间估计：30分钟
