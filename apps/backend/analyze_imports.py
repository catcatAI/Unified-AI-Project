import re
import json

# Parse import timing data
data = []
with open('import_timing.txt', 'r', encoding='utf-8') as f:
    for line in f:
        match = re.search(r'import time:\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(.+)', line)
        if match:
            self_time = int(match.group(1))
            cumulative = int(match.group(2))
            module = match.group(3).strip()
            data.append({
                'self_us': self_time,
                'cumulative_us': cumulative,
                'self_ms': self_time / 1000,
                'cumulative_ms': cumulative / 1000,
                'self_sec': self_time / 1000000,
                'cumulative_sec': cumulative / 1000000,
                'module': module
            })

# Sort by cumulative time
data.sort(key=lambda x: x['cumulative_us'], reverse=True)

print("=" * 100)
print("BACKEND IMPORT PERFORMANCE ANALYSIS")
print("=" * 100)
print()

# Top 30 slowest cumulative imports
print("TOP 30 SLOWEST CUMULATIVE IMPORTS (seconds):")
print("-" * 100)
print(f"{'Cumulative':>12} | {'Self':>10} | {'Module'}")
print("-" * 100)
for item in data[:30]:
    print(f"{item['cumulative_sec']:>11.2f}s | {item['self_sec']:>9.2f}s | {item['module']}")

print()
print("=" * 100)

# Identify blocking operations (> 1 second cumulative)
blocking = [x for x in data if x['cumulative_sec'] > 1.0 and not x['module'].startswith('src.')]
print(f"\nBLOCKING THIRD-PARTY MODULES (>1 second): {len(blocking)} modules")
print("-" * 100)
print(f"{'Cumulative':>12} | {'Module'}")
print("-" * 100)
for item in blocking[:20]:
    print(f"{item['cumulative_sec']:>11.2f}s | {item['module']}")

# Identify project modules that are slow
print()
print("=" * 100)
project_modules = [x for x in data if x['module'].startswith(('src.', 'ai.', 'api.', 'services.', 'economy.', 'pet.'))]
project_slow = [x for x in project_modules if x['cumulative_sec'] > 0.5]
print(f"\nSLOW PROJECT MODULES (>0.5 seconds): {len(project_slow)} modules")
print("-" * 100)
print(f"{'Cumulative':>12} | {'Self':>10} | {'Module'}")
print("-" * 100)
for item in project_slow:
    print(f"{item['cumulative_sec']:>11.2f}s | {item['self_sec']:>9.2f}s | {item['module']}")

# Save detailed report
with open('import_analysis.json', 'w') as f:
    json.dump({
        'total_time_seconds': data[0]['cumulative_sec'] if data else 0,
        'top_30_slowest': data[:30],
        'blocking_third_party': blocking[:20],
        'slow_project_modules': project_slow
    }, f, indent=2)

print()
print("=" * 100)
print(f"\n✓ Detailed report saved to: import_analysis.json")
print(f"✓ Total import time: {data[0]['cumulative_sec']:.2f} seconds" if data else "No data")
print()
