import sys
sys.path.insert(0, 'apps/backend/src')

from security.permission_control import PermissionControlSystem, PermissionContext, PermissionType

def main():
    pcs = PermissionControlSystem()
    print('Default rules count:', len(pcs.default_rules))
    
    # Print all default rules
    for i, rule in enumerate(pcs.default_rules):
        print(f'  {i}: {rule.permission_type.value} - {rule.allowed_actions}')
    
    # Test the specific case
    context = PermissionContext(
        user_id='ai_agent_1',
        operation=PermissionType.FILE_ACCESS.value,
        resource='/projects/test/file.txt',
        action='read'
    )
    
    print(f"Checking permission for:")
    print(f"  User: {context.user_id}")
    print(f"  Operation: {context.operation}")
    print(f"  Resource: {context.resource}")
    print(f"  Action: {context.action}")
    
    # Check each rule manually
    print("\nChecking rules:")
    for i, rule in enumerate(pcs.default_rules):
        if rule.permission_type.value == context.operation:
            print(f"  Rule {i} matches operation:")
            print(f"    Permission type: {rule.permission_type.value}")
            print(f"    Resource pattern: {rule.resource_pattern}")
            print(f"    Allowed actions: {rule.allowed_actions}")
            print(f"    Denied actions: {rule.denied_actions}")
            
            # Check resource pattern
            if rule.resource_pattern != "*" and not pcs._matches_pattern(context.resource, rule.resource_pattern):
                print(f"    Resource pattern does not match")
            else:
                print(f"    Resource pattern matches")
                
            # Check action
            if rule.denied_actions and context.action in rule.denied_actions:
                print(f"    Action is denied")
            elif rule.allowed_actions and context.action not in rule.allowed_actions:
                print(f"    Action is not allowed")
            else:
                print(f"    Action is allowed")
    
    result = pcs.check_permission(context)
    print('\nPermission check result:', result)

if __name__ == '__main__':
    main()