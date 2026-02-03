# Auto-Fix Workspace

This workspace contains all automatic repair systems and scripts for the Unified AI Project. These tools are designed to automatically detect and fix syntax errors, code issues, and other problems in the codebase.

## Directory Structure

- `scripts/` - Contains all automatic repair scripts
- `sandbox/` - Contains sandbox execution systems for safe code execution

## Auto-Fix Scripts

### Unified Auto-Fix System (Recommended)
1. `unified_auto_fix_system.py` - Unified system with comprehensive fixing capabilities
2. `interactive_auto_fix_system.py` - Interactive system with user-friendly interface

### Legacy Auto-Fix Scripts (Deprecated)
1. `auto_fix_syntax.py` - Basic syntax error fixing
2. `enhanced_auto_fix_syntax.py` - Enhanced syntax fixing with more patterns
3. `safe_auto_fix_syntax.py` - Syntax fixing with AST validation
4. `precision_auto_fix_syntax.py` - Line-by-line syntax fixing
5. `conservative_auto_fix_syntax.py` - Conservative approach to syntax fixing
6. `specialized_auto_fix.py` - Specialized fixing for missing colons
7. `comprehensive_auto_fix.py` - Comprehensive syntax error fixing
8. `precise_auto_fix.py` - Precise error fixing with detailed reporting
9. `advanced_auto_fix.py` - Advanced fixing with multiple strategies
10. `complete_auto_fix.py` - Complete fixing with multiple strategies

### Utility Scripts
1. `auto_fix_project.py` - Project-wide auto-fix execution
2. `check_auto_fix_updates.py` - Check for updates to auto-fix scripts
3. `test_enhanced_auto_fix.py` - Tests for enhanced auto-fix functionality
4. `unified_auto_fix.py` - Unified auto-fix interface

## Sandbox Systems

### sandbox_executor.py
Basic sandbox execution system for running code in isolated environments.

### enhanced_sandbox.py
Enhanced sandbox with security controls, resource limits, and permission checking.

## Usage

### Interactive Mode (Recommended)
```bash
python auto_fix_workspace/scripts/interactive_auto_fix_system.py
```

Follow the interactive prompts to:
1. Set files or code to fix
2. Start the fixing process
3. View results

### Unified Auto-Fix System
```bash
python auto_fix_workspace/scripts/unified_auto_fix_system.py
```

### Legacy Scripts
Most legacy scripts can be run directly:
```bash
python auto_fix_workspace/scripts/script_name.py
```

## Integration with Project

The project can call these auto-fix systems through:
1. Direct script execution
2. Integration with development tools
3. Automated testing workflows
4. CI/CD pipeline integration