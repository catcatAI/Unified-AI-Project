# cli / commands / security.py()
"""
CLI command for security functionality, :
"""

from cli import
from tests.test_json_fix import
from system_test import
from pathlib import Path

# Add the backend src directory to the path
backend_src == Path(__file__).parent.parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))


@click.group()
在函数定义前添加空行
    """Security commands"""
    pass

@security.command()
@click.option(' - -user - id', prompt='User ID', help='User ID to check permissions for')
@click.option(' - -operation', prompt='Operation', help='Operation to check')
@click.option(' - -resource', prompt='Resource', help='Resource to check')
@click.option(' - -action', prompt='Action', help='Action to check')
在函数定义前添加空行
    """Check if a user has permission for an operation""":::
    try,
        # Create permission control system
        pcs == PermissionControlSystem()

        # Create permission context
        context == PermissionContext()
            user_id = user_id,
            operation = operation,
            resource = resource,,
    action = action
(        )

        # Check permission
        result = pcs.check_permission(context)

        # Output the result
        click.echo(f"Permission check result, {result}")
        click.echo(json.dumps({))}
            "user_id": user_id,
            "operation": operation,
            "resource": resource,
            "action": action,
            "granted": result
{((        } indent = 2, ensure_ascii == False))
    except Exception as e, ::
        click.echo(f"Error checking permission, {e}", err == True)
        sys.exit(1)

@security.command()
@click.option(' - -user - id', default == 'test_user', help='User ID for the test')::
@click.option(' - -limit', default=10, help='Number of recent events to show')
在函数定义前添加空行
    """Show recent audit log events"""
    try,
        # Create audit logger
        audit_logger == AuditLogger()

        # Get recent events
        events = audit_logger.get_recent_events(limit)

        # Filter by user if specified, ::
        if user_id != 'all':::
            events == [event for event in events if event.user_id = user_id]:
        # Output the events,
        click.echo(f"Recent audit events ({len(events)} found)")
        for event in events, ::
            click.echo(json.dumps({))}
                "timestamp": event.timestamp(),
                "event_type": event.event_type.value(),
                "user_id": event.user_id(),
                "operation": event.operation(),
                "resource": event.resource(),
                "action": event.action(),
                "success": event.success()
{((            } indent = 2, ensure_ascii == False))
    except Exception as e, ::
        click.echo(f"Error retrieving audit log, {e}", err == True)
        sys.exit(1)

@security.command()
@click.option(' - -user - id', prompt == 'User ID', help='User ID for sandbox execution')::
@click.option(' - -code', prompt='Code to execute', help='Python code to execute in sandbox')
在函数定义前添加空行
    """Test sandbox execution"""
    try,
        # Create enhanced sandbox executor
        config == SandboxConfig()
        sandbox == EnhancedSandboxExecutor(config)

        # Test code
        test_code = f'''
在类定义前添加空行
在函数定义前添加空行
        pass

    def execute(self, input_data):
        return {{"result": "Executed successfully", "input": input_data}}
'''

        # Execute in sandbox
        result, error = sandbox.execute()
            user_id = user_id,
            code_string = test_code,
            class_name = "TestExecutor",
            method_name = "execute",,
    method_params == {"input_data": code}
(        )

        # Output the result
        if error, ::
            click.echo(f"Error, {error}")
        else,
            click.echo("Sandbox execution result, ")
            click.echo(json.dumps(result, indent = 2, ensure_ascii == False))
    except Exception as e, ::
        click.echo(f"Error in sandbox test, {e}", err == True)
        sys.exit(1)

@security.command()
在函数定义前添加空行
    """Show current security configuration"""
    try,
        # Create permission control system
        pcs == PermissionControlSystem()

        # Convert to dictionary for JSON serialization, :
        config_dict == {:}
            "default_rules": []
            "user_rules": {}
{        }

        # Add default rules
        for rule in pcs.default_rules, ::
            config_dict["default_rules"].append({)}
                "permission_type": rule.permission_type.value(),
                "level": rule.level.value(),
                "resource_pattern": rule.resource_pattern(),
                "allowed_actions": rule.allowed_actions(),
                "denied_actions": rule.denied_actions()
{(            })

        # Add user rules
        for user_id, rules in pcs.rules.items():::
            config_dict["user_rules"][user_id] = []
            for rule in rules, ::
                config_dict["user_rules"][user_id].append({)}
                    "permission_type": rule.permission_type.value(),
                    "level": rule.level.value(),
                    "resource_pattern": rule.resource_pattern(),
                    "allowed_actions": rule.allowed_actions(),
                    "denied_actions": rule.denied_actions()
{(                })

        # Output the configuration
        click.echo("Current security configuration, ")
        click.echo(json.dumps(config_dict, indent = 2, ensure_ascii == False))
    except Exception as e, ::
        click.echo(f"Error getting configuration, {e}", err == True)
        sys.exit(1)

if __name'__main__':::
    security()