import sys

# Read the file
with open('apps/backend/src/core/action_executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Remove autonomous=True and context from process_user_input calls
content = content.replace(
    '''result = await self.orchestrator.process_user_input(
                message,
                autonomous=True,
                context=context
            )''',
    '''result = await self.orchestrator.process_user_input(message)'''
)

# Fix 2: Remove autonomous param from life_cycle.py connect call if present
with open('apps/backend/src/core/autonomous/life_cycle.py', 'r', encoding='utf-8') as f:
    lc_content = f.read()

if 'autonomous=True' in lc_content:
    lc_content = lc_content.replace('autonomous=True,', '')
    with open('apps/backend/src/core/autonomous/life_cycle.py', 'w', encoding='utf-8') as f:
        f.write(lc_content)
    print("Fixed life_cycle.py")

# Write back
with open('apps/backend/src/core/action_executor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed action_executor.py")
print("Removed unsupported 'autonomous' parameter from process_user_input calls")
