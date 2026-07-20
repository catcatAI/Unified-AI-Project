"""Scan test files for assertion quality."""
import ast
import os

# === Part 1: Assertion quality ===
root = 'tests'
cats = {'A': [], 'B': [], 'C': [], 'D': []}

for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if not f.endswith('.py') or f.startswith('.'):
            continue
        fp = os.path.join(dirpath, f)
        rel = os.path.relpath(fp)

        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        has_real_assert = False
        has_test_fn = False
        has_skip = False

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith('test_'):
                    has_test_fn = True
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute):
                    a = fn.attr
                    if a in ('assertEqual', 'assertTrue', 'assertFalse', 'assertIn',
                             'assertIs', 'assertRaises', 'assertGreater', 'assertLess',
                             'assertAlmostEqual', 'assertNotEqual', 'assertIsNone',
                             'assertIsNotNone', 'assert_'):
                        has_real_assert = True
                    elif a in ('skip', 'skipif'):
                        has_skip = True
                elif isinstance(fn, ast.Name) and fn.id == 'assert':
                    has_real_assert = True

        if has_real_assert:
            cats['A'].append(rel)
        elif has_test_fn:
            cats['B'].append(rel)
        elif has_skip:
            cats['D'].append(rel)
        else:
            cats['C'].append(rel)

print('=== Test Quality Audit ===')
print(f'A - Has real assertions: {len(cats["A"])}')
print(f'B - Has test fns, weak:  {len(cats["B"])}')
print(f'C - No test functions:   {len(cats["C"])}')
print(f'D - Skip-only files:     {len(cats["D"])}')

if cats['B']:
    print('\n--- Weak tests (no real assertions) ---')
    for f in cats['B'][:20]:
        print(f'  {f}')

if cats['C']:
    print(f'\n--- No test functions ({len(cats["C"])}) ---')
    for f in cats['C'][:15]:
        print(f'  {f}')

# === Part 2: Orphan test file deeper investigation ===
print('\n\n=== Orphan Test File Analysis ===')
src_root = 'apps/backend/src'
orphans = []
matched = []

for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if not f.endswith('.py') or f == '__init__.py' or f == 'conftest.py':
            continue
        rel = os.path.relpath(os.path.join(dirpath, f), root)
        test_rel_no_ext = rel.rsplit('.', 1)[0]  # tests/ai/garden/test_foo

        # Check 1: exact mirror path exists in src
        src_path = os.path.join(src_root, test_rel_no_ext + '.py')
        if os.path.exists(src_path):
            matched.append(rel)
            continue

        # Check 2: corresponding __init__.py exists for dir
        src_dir_init = os.path.join(src_root, os.path.dirname(test_rel_no_ext), '__init__.py')
        if os.path.exists(src_dir_init):
            matched.append(rel)
            continue

        # Check 3: strip test_ prefix
        fname = os.path.basename(f)
        if fname.startswith('test_'):
            src_name = fname[5:]
            alt_dir = os.path.join(src_root, os.path.dirname(test_rel_no_ext))
            alt_path = os.path.join(alt_dir, src_name)
            if os.path.exists(alt_path):
                matched.append(rel)
                continue

        # Check 4: check if this is an integration test (may not have direct src mirror)
        parent_dir = os.path.basename(os.path.dirname(os.path.join(dirpath, f)))
        if parent_dir in ('integration', 'benchmarks', 'desktop', 'e2e'):
            matched.append(rel)
            continue

        orphans.append(rel)

print(f'Matched to source: {len(matched)}')
print(f'Truly orphan test files: {len(orphans)}')

if orphans:
    print('\n--- Orphan test files ---')
    for f in sorted(orphans):
        print(f'  {f}')
