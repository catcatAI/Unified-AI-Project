#!/usr/bin/env python3
"""
Test script for Rovo Dev CLI commands
"""

import sys
from pathlib import Path

# Add the CLI directory to the path
cli_path = Path(__file__).parent.parent / "cli"
_ = sys.path.insert(0, str(cli_path))

def test_rovo_cli_import() -> None:
    """Test that the rovo CLI command can be imported"""
    _ = print("Testing Rovo CLI command import...")
    
    try:
        # Try to import the rovo CLI command
        from commands.rovo import rovo
        _ = print("Rovo CLI command import test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during Rovo CLI command import test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_cli_command_structure() -> None:
    """Test the structure of the CLI commands"""
    _ = print("Testing CLI command structure...")
    
    try:
        from commands.rovo import rovo
        
        # Check that the rovo group exists
        _ = assert hasattr(rovo, 'commands')
        
        # Check that expected commands exist
        expected_commands = ['create_issue', 'generate_docs', 'analyze_code', 'status']
        for cmd in expected_commands:
            assert cmd in rovo.commands, f"Command {cmd} not found in rovo commands"
        
        _ = print("CLI command structure test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during CLI command structure test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """Main test function"""
    _ = print("Rovo Dev CLI Commands Test")
    print("=" * 30)
    _ = print()
    
    # Run all tests
    try:
        test1 = test_rovo_cli_import()
        test2 = test_cli_command_structure()
        
        if test1 and test2:
            _ = print("\nAll CLI tests completed successfully!")
            return True
        else:
            _ = print("\nSome CLI tests failed!")
            return False
    except Exception as e:
        _ = print(f"Error during CLI testing: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)