#!/usr/bin/env python3
"""
MCP Protocol Type Validation Script
MCP協議類型驗證腳本

Validates MCP type definitions and ensures compatibility between
legacy MCP and Context7 MCP implementations.
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

class MCPTypeValidator:
    """Validator for MCP type definitions."""

    def __init__(self) -> None:
        self.errors = []  # type: List[str]
        self.warnings = []  # type: List[str]
        self.type_definitions = {}  # type: Dict[str, Dict[str, Any]]

    def validate_mcp_types(self) -> None:
        """Validate MCP type definitions."""
        mcp_types_file = Path('src/mcp/types.py')

        if not mcp_types_file.exists():
            self.errors.append("MCP types file not found: src/mcp/types.py")
            return

        try:
            with open(mcp_types_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            self._extract_type_definitions(tree)
            self._validate_type_compatibility()
            self._validate_context7_types()

        except Exception as e:
            self.errors.append(f"Failed to parse MCP types: {e}")

    def _extract_type_definitions(self, tree: ast.AST) -> None:
        """Extract TypedDict definitions from AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a TypedDict
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'TypedDict':
                        self._analyze_typed_dict(node)

    def _analyze_typed_dict(self, node: ast.ClassDef) -> None:
        """Analyze a TypedDict class definition."""
        class_name = node.name
        fields = {}

        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                field_type = ast.unparse(item.annotation) if item.annotation else 'Any'
                fields[field_name] = field_type

        self.type_definitions[class_name] = {
            'fields': fields,
            'is_legacy': 'MCP' in class_name and 'Context' not in class_name,
            'is_context7': 'Context' in class_name or (class_name.startswith('MCP') and len(fields) > 5)
        }

    def _validate_type_compatibility(self) -> None:
        """Validate compatibility between legacy and Context7 types."""
        legacy_types = {name: info for name, info in self.type_definitions.items()
                       if info.get('is_legacy', False)}

        context7_types = {name: info for name, info in self.type_definitions.items()
                         if info.get('is_context7', False)}

        # Check for required legacy types
        required_legacy = {'MCPEnvelope', 'MCPCommandRequest', 'MCPCommandResponse'}
        missing_legacy = required_legacy - set(legacy_types.keys())

        if missing_legacy:
            self.errors.append(f"Missing required legacy MCP types: {missing_legacy}")

        # Check for required Context7 types
        required_context7 = {'MCPMessage', 'MCPResponse', 'MCPCapability'}
        missing_context7 = required_context7 - set(context7_types.keys())

        if missing_context7:
            self.errors.append(f"Missing required Context7 MCP types: {missing_context7}")

    def _validate_context7_types(self) -> None:
        """Validate Context7-specific type requirements."""
        context7_types = {name: info for name, info in self.type_definitions.items()
                         if info.get('is_context7', False)}

        # Validate MCPMessage structure
        if 'MCPMessage' in context7_types:
            mcp_message = context7_types['MCPMessage']
            required_fields = {'type', 'session_id', 'payload'}
            actual_fields = set(mcp_message['fields'].keys())

            missing_fields = required_fields - actual_fields
            if missing_fields:
                self.errors.append(f"MCPMessage missing required fields: {missing_fields}")

        # Validate MCPResponse structure
        if 'MCPResponse' in context7_types:
            mcp_response = context7_types['MCPResponse']
            required_fields = {'success', 'message_id', 'data'}
            actual_fields = set(mcp_response['fields'].keys())

            missing_fields = required_fields - actual_fields
            if missing_fields:
                self.errors.append(f"MCPResponse missing required fields: {missing_fields}")

        # Check for proper Optional typing
        for type_name, type_info in context7_types.items():
            for field_name, field_type in type_info['fields'].items():
                if 'Optional' not in field_type and field_name.endswith('_id'):
                    self.warnings.append(
                        f"{type_name}.{field_name} should probably be Optional[str]"
                    )

    def validate_mcp_connectors(self) -> None:
        """Validate MCP connector implementations."""
        # Check legacy connector
        legacy_connector = Path('src/mcp/connector.py')
        if legacy_connector.exists():
            self._validate_connector_file(legacy_connector, 'Legacy')

        # Check Context7 connector
        context7_connector = Path('src/mcp/context7_connector.py')
        if context7_connector.exists():
            self._validate_connector_file(context7_connector, 'Context7')
        else:
            self.warnings.append("Context7 connector not found")

    def _validate_connector_file(self, filepath: Path, connector_type: str) -> None:
        """Validate a specific connector file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for required methods
            if connector_type == 'Legacy':
                required_methods = ['connect', 'disconnect', 'send_command']
            else:  # Context7
                required_methods = ['connect', 'disconnect', 'send_context', 'request_context']

            for method in required_methods:
                if f"def {method}" not in content and f"async def {method}" not in content:
                    self.errors.append(f"{connector_type} connector missing method: {method}")

            # Check for proper error handling
            if 'try:' not in content or 'except' not in content:
                self.warnings.append(f"{connector_type} connector should have error handling")

        except Exception as e:
            self.errors.append(f"Failed to validate {connector_type} connector: {e}")

    def report(self) -> int:
        """Generate validation report."""
        total_issues = len(self.errors) + len(self.warnings)

        print("🔍 MCP Type Validation Report")
        print("=" * 40)

        if self.errors:
            print("\n🚨 ERRORS:")
            for error in self.errors:
                print(f"  ❌ {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")

        if total_issues == 0:
            print("\n✅ All MCP types are valid!")
            return 0
        else:
            print(f"\n📊 Found {len(self.errors)} errors and {len(self.warnings)} warnings")
            return 1 if self.errors else 0

def main() -> int:
    """Main entry point."""
    validator = MCPTypeValidator()

    print("Validating MCP type definitions...")
    validator.validate_mcp_types()

    print("Validating MCP connectors...")
    validator.validate_mcp_connectors()

    return validator.report()

if __name__ == '__main__':
    sys.exit(main())