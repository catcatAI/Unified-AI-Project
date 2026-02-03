# 测试结果处理组件集成指南

## 1. 安装依赖

确保已安装所有必要的依赖项：

```bash
pip install matplotlib seaborn pandas jinja2
```

或者使用项目中的requirements.txt：

```bash
pip install -r requirements.txt
```

## 2. 集成到现有测试流程

### 2.1 在测试完成后自动处理结果

在现有的测试脚本或CI/CD流程中添加以下代码：

```python
from apps.backend.scripts.process_test_results import process_test_results

# 在测试完成后调用
if __name__ == "__main__":
    # 假设测试结果保存在test_results.json中
    success = process_test_results(
        results_file="test_results.json",
        baseline_file="baseline_results.json",  # 可选，用于性能回归检测
        historical_files=["historical_results_1.json", "historical_results_2.json"],  # 可选，用于趋势分析
        send_email=True,  # 是否发送邮件通知
        recipient_emails=["dev-team@example.com"]  # 邮件接收者
    )
    
    if success:
        print("测试结果处理完成")
    else:
        print("测试结果处理失败")
```

### 2.2 手动处理测试结果

也可以通过命令行手动处理测试结果：

```bash
cd D:\Projects\Unified-AI-Project
python apps/backend/scripts/process_test_results.py test_results.json --baseline baseline_results.json --historical historical_results_1.json historical_results_2.json --send-email --recipients dev-team@example.com
```

## 3. 自定义配置

### 3.1 修改可视化样式

可以通过修改[test_result_visualizer.py](file:///D:/Projects/Unified-AI-Project/apps/backend/scripts/test_result_visualizer.py)中的matplotlib设置来自定义图表样式：

```python
# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

### 3.2 自定义反馈报告模板

反馈报告模板位于[templates/feedback_template.html](file:///D:/Projects/Unified-AI-Project/apps/backend/test_data/templates/feedback_template.html)，可以根据需要修改HTML和CSS样式。

### 3.3 调整分析参数

在[test_result_analyzer.py](file:///D:/Projects/Unified-AI-Project/apps/backend/scripts/test_result_analyzer.py)中可以调整分析参数：

```python
# 性能回归检测阈值（默认10%）
threshold: float = 0.1
```

## 4. 生成的报告和文件

处理完成后，将在[test_reports](file:///D:/Projects/Unified-AI-Project/apps/backend/test_data/test_reports)目录中生成以下文件：

1. `test_distribution.png` - 测试结果分布饼图
2. `test_trends.png` - 测试趋势折线图（如果有历史数据）
3. `visualization_report.html` - 可视化报告
4. `analysis_report.json` - 详细的分析报告
5. `feedback_report.html` - 反馈报告
6. `improvement_tasks.json` - 改进建议任务列表

## 5. 故障排除

### 5.1 字体警告

如果看到中文字体警告，可以：

1. 安装中文字体包
2. 修改脚本中的字体设置
3. 忽略警告（不影响功能）

### 5.2 文件路径问题

确保测试结果文件路径正确，并且有读取权限。

### 5.3 依赖项问题

确保所有依赖项都已正确安装：

```bash
pip list | grep -E "matplotlib|seaborn|pandas|jinja2"
```

## 6. 最佳实践

1. **定期运行**：建议在每次测试完成后自动运行结果处理脚本
2. **保存历史数据**：保留历史测试结果用于趋势分析
3. **设置基线**：建立性能基线用于回归检测
4. **关注反馈**：定期查看生成的改进建议并采取行动
5. **自定义模板**：根据团队需求自定义反馈报告模板