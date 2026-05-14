import sys
sys.path.insert(0, 'apps/backend/src')
from ai.code_inspection import create_inspector

inspector = create_inspector('apps/backend/src')
result = inspector.inspect()

print('=' * 60)
print('ANGELA CODE INSPECTION REPORT')
print('=' * 60)
print(f'Total issues:     {result["total_issues"]}')
print(f'Auto-fixable:      {result["auto_fixable"]}')
print(f'Critical:          {result["critical"]}')
print(f'High:              {result["high"]}')
print(f'Medium:            {result["medium"]}')
print(f'Low:               {result["low"]}')
print()

status = inspector.get_status()
kg = status['knowledge_graph']
print('KNOWLEDGE GRAPH:')
print(f'  Total nodes:     {kg["total_nodes"]}')
print(f'  Total edges:     {kg["total_edges"]}')
print(f'  Files:           {kg.get("files", 0)}')
print(f'  Classes:         {kg.get("classes", 0)}')
print(f'  Functions:       {kg.get("functions", 0)}')
print()

lr = status['learning']
print('LEARNING ENGINE:')
print(f'  Patterns:        {lr["patterns_count"]}')
print(f'  High confidence: {lr["high_confidence_patterns"]}')
print(f'  Total feedback:   {lr["total_feedback"]}')
print(f'  Acceptance rate: {lr["acceptance_rate"]:.0%}')
print()

# Show top issues
if result['total_issues'] > 0:
    issues = result['report'].issues[:20]
    print('TOP ISSUES:')
    for issue in issues:
        print(f'  [{issue.severity.value.upper():8}] {issue.id} | {issue.category.value:12} | {issue.file.split("/")[-1]}:{issue.line}')
        print(f'         {issue.description[:60]}')
print()
print('=' * 60)