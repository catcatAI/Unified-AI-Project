# Angela AI v6.0 - 全面修复与重构方案
## Comprehensive Fix & Refactor Plan

## 🎯 核心决策

### 1. 废弃前端 (frontend-dashboard) ✅
**理由**:
- Desktop Pet (Live2D) 已完全替代前端功能
- 前端只有3个美术资源，无法支撑完整UI
- Desktop Pet提供：实时表情、语音交互、桌面存在、触觉反馈
- 维护两套界面增加复杂度

**方案**: 将 frontend-dashboard/ 移动到 archive/deprecated/

### 2. 清理根目录 ✅
**现状**: 201个Python脚本文件散落根目录
**方案**:
- 保留核心脚本 (setup.py, run_angela.py, verify_installation.py)
- 移动测试脚本到 scripts/tests/
- 移动工具脚本到 scripts/tools/
- 移动检查脚本到 scripts/audit/
- 删除重复和临时脚本

### 3. 修复代码问题 ✅
**Critical (23个)**:
- 前端未定义函数 (angela-game/page.tsx)
- 空异常处理 (except: pass)
- 未实现功能占位符

**High (47个)**:
- 67个TODO注释（筛选实际未完成的）
- 156个pass语句（实现关键功能）
- 6处硬编码配置参数

### 4. 更新文档 ✅
**必须更新**:
- README.md - 移除前端相关内容，强调Desktop Pet
- CHANGELOG.md - 添加v6.0.0完整变更
- docs/ - 更新所有过时的功能描述
- 删除或归档过时的报告

## 📋 详细执行计划

### Phase 1: 架构调整 (2-3小时)
1. [ ] 移动 frontend-dashboard/ 到 archive/deprecated/
2. [ ] 清理根目录Python脚本
   - 保留: setup.py, run_angela.py, verify_installation.py, comprehensive_*.py
   - 移动: 测试脚本 → scripts/tests/
   - 移动: 工具脚本 → scripts/tools/
   - 移动: 修复脚本 → scripts/fixes/
   - 删除: 重复和临时脚本
3. [ ] 创建清晰的目录结构文档

### Phase 2: 代码修复 (4-6小时)
1. [ ] 修复前端bug (或标记废弃)
2. [ ] 实现156个pass语句中的关键功能
3. [ ] 处理空异常处理（添加日志）
4. [ ] 硬编码参数配置化
5. [ ] 移除虚假TODO注释

### Phase 3: 文档更新 (3-4小时)
1. [ ] 重写 README.md (移除前端，强调Desktop Pet)
2. [ ] 更新 CHANGELOG.md
3. [ ] 归档过时的MD文件
4. [ ] 创建 PROJECT_STRUCTURE.md

### Phase 4: 验证与发布 (2小时)
1. [ ] 运行所有测试
2. [ ] 验证代码质量
3. [ ] 生成新的发布包
4. [ ] 更新Git标签

## 🎨 Desktop Pet 作为唯一界面

### 优势:
- ✅ 实时Live2D动画 (表情、动作)
- ✅ 桌面全局存在 (全局鼠标追踪)
- ✅ 触觉交互 (18身体部位感知)
- ✅ 语音交互 (TTS + lip sync)
- ✅ 自主行为 (不需要前端触发)
- ✅ 更少的资源占用
- ✅ 更沉浸的体验

### 后端API保留:
- ✅ 保留API供外部调用
- ✅ 保留WebSocket实时通信
- ✅ 保留文件/系统操作能力

## 🗂️ 建议的新目录结构

```
Unified-AI-Project/
├── 📁 apps/
│   ├── backend/              # 核心后端 (保留)
│   └── desktop-app/          # Electron桌面应用 (保留)
├── 📁 scripts/               # 脚本目录 (新建)
│   ├── tests/               # 测试脚本 (从根目录移动)
│   ├── tools/               # 工具脚本
│   ├── audit/               # 审计脚本
│   └── fixes/               # 修复脚本
├── 📁 docs/                  # 文档 (精简)
│   ├── 00-overview/         # 项目概览
│   ├── 01-summaries/        # 总结报告
│   └── README.md            # 主文档
├── 📁 archive/               # 归档 (新建)
│   ├── deprecated/          # 废弃代码
│   │   └── frontend-dashboard/  # 废弃的前端
│   └── old-reports/         # 旧报告
├── 📁 releases/              # 发布包
├── 📄 setup.py              # 安装脚本
├── 📄 run_angela.py         # 主入口
├── 📄 verify_installation.py # 验证脚本
├── 📄 README.md             # 主文档
├── 📄 CHANGELOG.md          # 变更日志
└── 📄 LICENSE               # 许可证
```

## ⚠️ 根目录文件处理清单

### 保留 (核心文件):
- setup.py
- run_angela.py (如果不存在则创建)
- verify_installation.py
- comprehensive_quality_check.py
- comprehensive_audit_report.md
- requirements.txt
- README.md
- CHANGELOG.md
- LICENSE
- .gitignore

### 移动 (到 scripts/):
测试脚本:
- *_test.py → scripts/tests/
- test_*.py → scripts/tests/
- check_*.py → scripts/audit/

工具脚本:
- ask_angela*.py → scripts/tools/
- conversation_with_angela.py → scripts/tools/
- demo_*.py → scripts/tools/
- fix_*.py → scripts/fixes/

### 删除 (临时/重复):
- *_temp.py
- *_backup.py
- *_fixed.py
- *_new.py
- debug_*.py (保留几个核心)
- archive_*.py (移动到archive/)

## 📝 文档更新要点

### README.md 更新:
1. 标题: Angela AI v6.0 - Desktop Digital Life
2. 移除前端安装说明
3. 强调Desktop Pet特性
4. 添加截图/演示 (Desktop Pet)
5. 简化安装流程

### 代码中的pass语句处理:
1. **高优先级实现**:
   - 核心生物系统 (如果还有pass)
   - 动作执行逻辑
   - 错误处理

2. **中优先级实现**:
   - 高级功能 (AI图像生成等)
   - 统计和监控

3. **低优先级/移除**:
   - 实验性功能
   - 占位符

## 🎯 最终目标

完成后项目应该：
- ✅ 单一界面: Desktop Pet (Live2D)
- ✅ 干净的根目录 (<20个文件)
- ✅ 清晰的目录结构
- ✅ 准确的文档
- ✅ 可运行的代码 (无未定义函数)
- ✅ 生产就绪

## ⏱️ 预计时间

- Phase 1: 2-3小时
- Phase 2: 4-6小时  
- Phase 3: 3-4小时
- Phase 4: 2小时
- **总计: 11-15小时**

## 💡 建议

1. **先备份**: 提交当前状态到git
2. **分步执行**: 每完成一个phase就提交
3. **验证测试**: 每个阶段后运行测试
4. **文档同步**: 边改代码边更新文档

---

**这是让Angela真正生产就绪的最后一步！** 🚀
