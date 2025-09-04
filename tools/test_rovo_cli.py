#!/usr/bin/env python3
"""
Test script for Rovo Dev CLI commands
"""

import sys
from pathlib import Path

# Add the CLI directory to the path
cli_path = Path(__file__).parent.parent / "cli"
sys.path.insert(0, str(cli_path))

def test_rovo_cli_import():
    """Test that the rovo CLI command can be imported"""
    print("Testing Rovo CLI command import...")
    
    try:
        # Try to import the rovo CLI command
        from commands.rovo import rovo
        print("Rovo CLI command import test passed!")
        return True
    except Exception as e:
        print(f"Error during Rovo CLI command import test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_command_structure():
    """Test the structure of the CLI commands"""
    print("Testing CLI command structure...")
    
    try:
        from commands.rovo import rovo
        
        # Check that the rovo group exists
        assert hasattr(rovo, 'commands')
        
        # Check that expected commands exist
        expected_commands = ['create_issue', 'generate_docs', 'analyze_code', 'status']
        for cmd in expected_commands:
            assert cmd in rovo.commands, f"Command {cmd} not found in rovo commands"
        
        print("CLI command structure test passed!")
        return True
    except Exception as e:
        print(f"Error during CLI command structure test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Rovo Dev CLI Commands Test")
    print("=" * 30)
    print()
    
    # Run all tests
    try:
        test1 = test_rovo_cli_import()
        test2 = test_cli_command_structure()
        
        if test1 and test2:
            print("\nAll CLI tests completed successfully!")
            return True
        else:
            print("\nSome CLI tests failed!")
            return False
    except Exception as e:
        print(f"Error during CLI testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)