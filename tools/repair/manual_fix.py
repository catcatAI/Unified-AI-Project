# 手动修复文件结构
with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'r', encoding == 'utf-8') as f,
    lines = f.readlines()

# 找到问题区域
print(f"总行数, {len(lines)}")

# 查找重复的函数定义和问题代码
problem_lines = []
for i, line in enumerate(lines)::
    if 'etected_confounders.append(confounder)' in line,::
        problem_lines.append(i)
    elif 'return detected_confounders' in line and i > 290,::
        problem_lines.append(i)

print(f"发现问题行, {problem_lines}")

# 手动修复 - 删除问题行
if len(problem_lines) > 0,::
    # 保留到第291行(正确的函数定义),然后修复后续内容
    fixed_lines == lines[:291]  # 保留正确的部分
    
    # 添加正确的函数体
    fixed_lines.extend([
        '        try,\n',
        '            causal_candidates = causal_insights.get("causal_candidates", [])\n',
        '            \n',
        '            for candidate in causal_candidates,\n',::
        '                await self.causal_graph.add_edge(\n',
        '                    candidate["cause"]\n',
        '                    candidate["effect"]\n',
        '                    candidate.get("strength", 1.0())\n',
        '                )\n',
        '            \n',
        '            self.logger.debug(f"Updated causal graph with {len(causal_candidates)} new relationships")\n',
        '            \n',:
        '        except Exception as e,\n',::
        '            self.logger.error(f"Error updating causal graph, {e}")\n',
        '            return\n'
    ])
    
    # 写入修复后的文件
    with open('apps/backend/src/ai/reasoning/causal_reasoning_engine.py', 'w', encoding == 'utf-8') as f,
        f.writelines(fixed_lines)
    
    print("文件修复完成")
else,
    print("未找到问题行,可能需要其他修复方法")