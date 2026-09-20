# HAM自动删除机制改进实施文档

## 🎯 概述

本文档详细描述了对HAM（Hierarchical Abstractive
Memory）自动删除机制的改进方案和实施步骤，旨在提升记忆管理的智能化水平和系统性能。

## 🏗️ 当前实现分析

### 核心组件

1. [_perform_deletion_check](../apps/backend/src/ai/memory/ham_memory_manager.py)：执行内存清理检查的核心方法
2. [_delete_old_experiences](../apps/backend/src/ai/memory/ham_memory_manager.py)：后台定期运行的删除任务
3. [PersonalityManager](../apps/backend/src/ai/personality/personality_manager.py)：提供个性化配置[memory_retention](../apps/backend/configs/personality_profiles/miko_base.json)

### 当前策略

1. 基于系统内存使用率触发删除
2. 根据[memory_retention](../apps/backend/configs/personality_profiles/miko_base.json)特性确定删除阈值
3. 按相关性和时间戳排序未保护的记忆
4. 从低优先级记忆开始删除直到内存使用回到可接受范围

## 🚀 改进方案

### 1. 多维度删除策略

#### 1.1 新增评估维度

- **记忆类型权重**：不同类型的记忆具有不同的保留价值
- **访问频率**：经常被访问的记忆具有更高的保留价值
- **上下文重要性**：与当前任务或对话上下文相关的记忆应优先保留
- **关联度**：与其他重要记忆关联的记忆应优先保留

#### 1.2 实现方案

```python
class MemoryEvaluationEngine:
    def evaluate_memory_value(self, memory_id, memory_data):
        """
        评估记忆的价值分数
        返回0-1之间的分数，1表示最有价值
        """
        # 类型权重 (0.2权重)
        type_weight = self.get_type_weight(memory_data.get("data_type"))

        # 访问频率 (0.3权重)
        access_frequency = self.calculate_access_frequency(memory_id)

        # 上下文重要性 (0.3权重)
        context_importance = self.calculate_context_importance(memory_id)

        # 关联度 (0.2权重)
       关联度 = self.calculate关联度(memory_id)

        # 综合评分
        value_score = (
            type_weight * 0.2 +
            access_frequency * 0.3 +
            context_importance * 0.3 +
            关联度 * 0.2
        )

        return value_score
```

### 2. 个性化配置改进

#### 2.1 动态调整[memory_retention](../apps/backend/configs/personality_profiles/miko_base.json)

```python
class DynamicMemoryRetention:
    def adjust_retention_rate(self, system_load, user_activity, memory_pressure):
        """
        根据系统状态动态调整memory_retention值
        """
        base_retention = self.personality_manager.get_current_personality_trait("memory_retention", 0.5)

        # 根据系统负载调整
        load_factor = self.calculate_load_factor(system_load)  # -0.1 to +0.1

        # 根据用户活动调整
        activity_factor = self.calculate_activity_factor(user_activity)  # -0.1 to +0.1

        # 根据内存压力调整
        pressure_factor = self.calculate_pressure_factor(memory_pressure)  # -0.2 to 0

        adjusted_retention = base_retention + load_factor + activity_factor + pressure_factor

        # 确保在合理范围内
        return max(0.1, min(0.9, adjusted_retention))
```

#### 2.2 用户可配置策略

```json
{
  "memory_management": {
    "strategies": {
      "conservative": {
        "description": "保守策略，尽可能保留记忆",
        "priority_factors": {
          "type_weight": 0.4,
          "access_frequency": 0.3,
          "context_importance": 0.2,
          "关联度": 0.1
        }
      },
      "balanced": {
        "description": "平衡策略，综合考虑各种因素",
        "priority_factors": {
          "type_weight": 0.25,
          "access_frequency": 0.25,
          "context_importance": 0.25,
          "关联度": 0.25
        }
      },
      "aggressive": {
        "description": "激进策略，优先释放内存",
        "priority_factors": {
          "type_weight": 0.1,
          "access_frequency": 0.2,
          "context_importance": 0.3,
          "关联度": 0.4
        }
      }
    },
    "default_strategy": "balanced"
  }
}
```

### 3. 性能优化

#### 3.1 分批删除机制

```python
async def _delete_old_experiences_batched(self, batch_size=50):
    """
    分批执行删除操作，避免阻塞系统
    """
    while True:
        deletion_interval = max(60, 3600 - len(self.core_memory_store) * 10)
        await asyncio.sleep(deletion_interval)

        # 分批处理删除
        deleted_count = 0
        while self._should_continue_deletion() and deleted_count < batch_size:
            deleted = await asyncio.to_thread(self._perform_deletion_check_batch)
            if deleted:
                deleted_count += deleted
                # 每批之间短暂休息
                await asyncio.sleep(0.1)
            else:
                break
```

#### 3.2 高效数据结构

使用优先队列维护记忆排序：

```python
import heapq

class MemoryPriorityQueue:
    def __init__(self):
        self.heap = []
        self.entry_map = {}

    def add_memory(self, memory_id, priority):
        # 使用堆维护优先级排序
        entry = [-priority, memory_id]  # 负值实现最大堆
        self.entry_map[memory_id] = entry
        heapq.heappush(self.heap, entry)

    def remove_memory(self, memory_id):
        if memory_id in self.entry_map:
            entry = self.entry_map.pop(memory_id)
            entry[-1] = None  # 标记为已删除

    def get_highest_priority(self):
        while self.heap:
            priority, memory_id = heapq.heappop(self.heap)
            if memory_id is not None:
                del self.entry_map[memory_id]
                return memory_id, -priority
        return None, None
```

### 4. 安全性增强

#### 4.1 删除前备份

```python
class MemoryBackupManager:
    def backup_memory_before_deletion(self, memory_id, memory_data):
        """
        在删除前备份记忆到临时存储
        """
        backup_id = f"backup_{memory_id}_{int(time.time())}"
        backup_data = {
            "original_id": memory_id,
            "data": memory_data,
            "backup_time": time.time(),
            "reason": "auto_delete"
        }

        # 存储到备份区域
        self.backup_store[backup_id] = backup_data

        # 定期清理旧备份
        self._cleanup_old_backups()

        return backup_id
```

#### 4.2 删除确认机制

```python
def _perform_deletion_check_with_confirmation(self):
    """
    带确认机制的删除检查
    """
    # ... 现有检查逻辑 ...

    # 对于重要记忆，需要确认
    important_memories = []
    regular_memories = []

    for memory_id, data_pkg in memories_to_consider:
        if self._is_important_memory(data_pkg):
            important_memories.append((memory_id, data_pkg))
        else:
            regular_memories.append((memory_id, data_pkg))

    # 直接删除普通记忆
    for memory_id, _ in regular_memories:
        self._delete_memory_with_backup(memory_id)

    # 对重要记忆触发确认流程
    if important_memories:
        self._trigger_important_memory_confirmation(important_memories)
```

## 📅 实施步骤

### 阶段1：设计与原型 (2周)

1. 完成详细技术设计文档
2. 实现评估引擎原型
3. 设计新的数据结构

### 阶段2：核心功能实现 (4周)

1. 实现多维度评估算法
2. 实现动态[memory_retention](../apps/backend/configs/personality_profiles/miko_base.json)调整机制
3. 实现分批删除机制
4. 实现高效数据结构

### 阶段3：安全性增强 (2周)

1. 实现备份机制
2. 实现删除确认机制
3. 实现用户配置接口

### 阶段4：测试与优化 (3周)

1. 单元测试
2. 集成测试
3. 性能测试
4. 根据测试结果优化

### 阶段5：文档与部署 (1周)

1. 更新相关文档
2. 部署到测试环境
3. 用户培训和文档发布

## 🧪 测试计划

### 单元测试

1. 测试记忆价值评估算法的正确性
2. 测试动态[memory_retention](../apps/backend/configs/personality_profiles/miko_base.json)调整逻辑
3. 测试分批删除机制
4. 测试备份和恢复功能

### 集成测试

1. 测试整个删除流程的正确性
2. 测试与现有系统的兼容性
3. 测试异常情况处理

### 性能测试

1. 测试高负载下的删除性能
2. 测试内存使用效率
3. 测试响应时间

## 📊 预期效果

### 性能指标

- 删除操作响应时间减少30%
- 系统内存使用效率提升20%
- 高负载下系统稳定性提升

### 功能指标

- 记忆保留准确率提升至95%以上
- 用户对记忆管理满意度提升
- 重要记忆误删率降低至0.1%以下

## 🛠️ 技术依赖

1. **psutil**：系统资源监控
2. **heapq**：优先队列实现
3. **asyncio**：异步处理
4. **机器学习库**：智能评估算法（如scikit-learn）

## 📝 后续优化方向

1. **机器学习模型**：训练专门的模型来预测记忆价值
2. **用户行为分析**：根据用户行为模式优化删除策略
3. **跨会话记忆管理**：实现跨会话的记忆保留策略
4. **云存储集成**：将低优先级记忆迁移到云存储

---

**文档版本**: v1.0  
**创建日期**: 2025年8月25日  
**最后更新**: 2025年8月25日
