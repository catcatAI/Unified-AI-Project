#!/usr/bin/env python3
"""
Comprehensive Unified AI Project Audit Script

This script performs a systematic audit of the entire project to identify:
1. Unfinished components (TODO/FIXME/NotImplemented)
2. Missing implementations (stub methods)
3. Integration gaps between components
4. Configuration completeness
5. API endpoint implementation status
6. Frontend-backend connectivity issues
7. Database schema completeness
8. Testing coverage gaps
"""

import os
import re
import json
import ast
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AuditIssue:
    """Represents an audit issue found in the codebase."""
    category: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    line_number: int
    description: str
    code_snippet: str
    component: str

class ComprehensiveAuditor:
    """Performs comprehensive audit of the Unified AI Project."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[AuditIssue] = []
        self.component_status: Dict[str, Dict] = {}
        
        # Patterns to search for
        self.todo_patterns = [
            re.compile(r'#\s*TODO\b', re.IGNORECASE),
            re.compile(r'#\s*FIXME\b', re.IGNORECASE),
            re.compile(r'raise\s+NotImplementedError', re.IGNORECASE),
            re.compile(r'pass\s*#\s*(todo|fixme|placeholder)', re.IGNORECASE),
            re.compile(r'placeholder', re.IGNORECASE),
            re.compile(r'stub\b', re.IGNORECASE),
        ]
        
        # Core components to check
        self.core_components = [
            'backend/src/core',
            'backend/src/api',
            'backend/src/services',
            'backend/src/ai',
            'backend/src/game',
            'frontend-dashboard/src',
            'desktop-app/src'
        ]
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run the complete audit and return comprehensive report."""
        print("🔍 Starting Comprehensive Unified AI Project Audit...")
        
        # 1. Core System Components Analysis
        await self.audit_core_components()
        
        # 2. Integration Points Analysis
        await self.audit_integration_points()
        
        # 3. Configuration Files Analysis
        await self.audit_configuration_files()
        
        # 4. API Endpoints Analysis
        await self.audit_api_endpoints()
        
        # 5. Frontend-Backend Integration
        await self.audit_frontend_backend_integration()
        
        # 6. Database Schema Analysis
        await self.audit_database_schemas()
        
        # 7. Testing Coverage Analysis
        await self.audit_testing_coverage()
        
        # 8. Missing Implementation Analysis
        await self.audit_missing_implementations()
        
        # Generate final report
        return self.generate_comprehensive_report()
    
    async def audit_core_components(self):
        """Audit all core system components for completeness."""
        print("\n📋 Auditing Core Components...")
        
        core_path = self.project_root / "apps/backend/src/core"
        if not core_path.exists():
            self.add_issue(
                "core_components", "critical", str(core_path), 0,
                "Core components directory not found", "", "core"
            )
            return
        
        for file_path in core_path.rglob("*.py"):
            self.check_file_for_issues(file_path, "core")
            
        # Check specific critical components
        critical_files = [
            "core/managers/system_manager.py",
            "core/orchestrator_actor.py",
            "core/security/security_manager.py",
            "core/knowledge/knowledge_manager.py"
        ]
        
        for rel_path in critical_files:
            full_path = self.project_root / "apps/backend/src" / rel_path
            if not full_path.exists():
                self.add_issue(
                    "core_components", "critical", str(full_path), 0,
                    f"Critical component missing: {rel_path}", "", "core"
                )
    
    async def audit_integration_points(self):
        """Audit integration points between system components."""
        print("\n🔗 Auditing Integration Points...")
        
        # Check service integrations
        services_path = self.project_root / "apps/backend/src/services"
        if services_path.exists():
            for service_file in services_path.glob("*_service.py"):
                self.check_service_integration(service_file)
        
        # Check API route integrations
        api_path = self.project_root / "apps/backend/src/api"
        if api_path.exists():
            for route_file in api_path.rglob("*.py"):
                if route_file.name != "__init__.py":
                    self.check_api_integration(route_file)
    
    async def audit_configuration_files(self):
        """Audit configuration files for completeness."""
        print("\n⚙️ Auditing Configuration Files...")
        
        config_paths = [
            "apps/backend/configs/config.yaml",
            "apps/backend/configs/multi_llm_config.json",
            "apps/backend/configs/chromadb_config.json",
            "apps/backend/package.json",
            "package.json"
        ]
        
        for config_path in config_paths:
            full_path = self.project_root / config_path
            if not full_path.exists():
                self.add_issue(
                    "configuration", "high", str(full_path), 0,
                    f"Configuration file missing: {config_path}", "", "config"
                )
            else:
                self.validate_configuration_file(full_path)
    
    async def audit_api_endpoints(self):
        """Audit API endpoints for proper implementation."""
        print("\n🌐 Auditing API Endpoints...")
        
        api_path = self.project_root / "apps/backend/src/api/v1/endpoints"
        if not api_path.exists():
            self.add_issue(
                "api_endpoints", "critical", str(api_path), 0,
                "API endpoints directory not found", "", "api"
            )
            return
        
        # Check each endpoint file
        for endpoint_file in api_path.glob("*.py"):
            if endpoint_file.name != "__init__.py":
                self.check_endpoint_implementation(endpoint_file)
    
    async def audit_frontend_backend_integration(self):
        """Audit frontend-backend integration points."""
        print("\n🖥️ Auditing Frontend-Backend Integration...")
        
        frontend_path = self.project_root / "apps/frontend-dashboard/src"
        backend_path = self.project_root / "apps/backend/src"
        
        if not frontend_path.exists():
            self.add_issue(
                "frontend_integration", "critical", str(frontend_path), 0,
                "Frontend directory not found", "", "frontend"
            )
            return
        
        # Check API route consistency
        frontend_api_routes = list(frontend_path.rglob("api/**/route.ts"))
        backend_endpoints = list(backend_path.rglob("api/**/endpoints/*.py"))
        
        # Map expected API endpoints
        expected_apis = {
            "/api/v1/chat": ["frontend"],
            "/api/v1/pet": ["frontend"],
            "/api/v1/economy": ["frontend"],
            "/api/v1/llm": ["frontend"],
            "/api/v1/tools": ["frontend"]
        }
        
        for api_path, consumers in expected_apis.items():
            backend_file = backend_path / f"v1/endpoints/{api_path.split('/')[-1]}.py"
            if not backend_file.exists():
                self.add_issue(
                    "frontend_integration", "high", str(backend_file), 0,
                    f"Backend API endpoint missing: {api_path}", "", "integration"
                )
    
    async def audit_database_schemas(self):
        """Audit database schemas and data models."""
        print("\n🗄️ Auditing Database Schemas...")
        
        # Check for database files
        db_files = list(self.project_root.rglob("*.db"))
        
        if len(db_files) == 0:
            self.add_issue(
                "database", "medium", "", 0,
                "No database files found - may need initialization", "", "database"
            )
        
        # Check for schema definitions
        schema_files = list(self.project_root.rglob("*schema*.py"))
        schema_files.extend(list(self.project_root.rglob("*models*.py")))
        
        if len(schema_files) == 0:
            self.add_issue(
                "database", "high", "", 0,
                "No database schema or model files found", "", "database"
            )
    
    async def audit_testing_coverage(self):
        """Audit testing coverage and test files."""
        print("\n🧪 Auditing Testing Coverage...")
        
        test_dirs = [
            "apps/backend/tests",
            "apps/frontend-dashboard/__tests__",
            "apps/desktop-app/__tests__"
        ]
        
        for test_dir in test_dirs:
            full_path = self.project_root / test_dir
            if not full_path.exists():
                self.add_issue(
                    "testing", "medium", str(full_path), 0,
                    f"Test directory missing: {test_dir}", "", "testing"
                )
            else:
                test_files = list(full_path.rglob("test_*.py"))
                if len(test_files) == 0:
                    self.add_issue(
                        "testing", "medium", str(full_path), 0,
                        f"No test files found in {test_dir}", "", "testing"
                    )
    
    async def audit_missing_implementations(self):
        """Audit for missing implementations and stub methods."""
        print("\n❌ Auditing Missing Implementations...")
        
        # Search through all Python files for TODO/FIXME/etc.
        for py_file in self.project_root.rglob("*.py"):
            # Skip virtual environment and node_modules
            if any(skip in str(py_file) for skip in ['.venv', 'node_modules', '__pycache__']):
                continue
            
            self.check_file_for_issues(py_file, "implementation")
    
    def check_file_for_issues(self, file_path: Path, category: str):
        """Check a single file for various types of issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            self.add_issue(
                category, "low", str(file_path), 0,
                f"Could not read file: {e}", "", "file_io"
            )
            return
        
        for i, line in enumerate(lines, 1):
            for pattern in self.todo_patterns:
                if pattern.search(line):
                    severity = self.determine_severity(line, file_path)
                    self.add_issue(
                        category, severity, str(file_path), i,
                        f"Found issue pattern: {pattern.pattern}", line.strip(), "code_quality"
                    )
    
    def determine_severity(self, line: str, file_path: str) -> str:
        """Determine severity of an issue based on content and location."""
        line_lower = line.lower()
        
        # Critical issues
        if 'notimplementederror' in line_lower:
            return "critical"
        if 'critical' in line_lower:
            return "critical"
        
        # High issues
        if 'todo' in line_lower and ('api' in str(file_path).lower() or 'endpoint' in str(file_path).lower()):
            return "high"
        if 'fixme' in line_lower:
            return "high"
        
        # Medium issues
        if 'todo' in line_lower:
            return "medium"
        if 'placeholder' in line_lower:
            return "medium"
        
        return "low"
    
    def check_service_integration(self, service_file: Path):
        """Check if a service is properly integrated."""
        try:
            with open(service_file, 'r') as f:
                content = f.read()
            
            # Check for placeholder implementation
            if 'placeholder' in content.lower():
                self.add_issue(
                    "integration", "high", str(service_file), 0,
                    f"Service contains placeholder implementation: {service_file.name}", "", "services"
                )
            
            # Check if service is registered in component registry
            registry_file = self.project_root / "apps/backend/src/core/managers/component_registry.py"
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry_content = f.read()
                
                service_name = service_file.stem.replace('_service', '')
                if service_name not in registry_content:
                    self.add_issue(
                        "integration", "medium", str(service_file), 0,
                        f"Service may not be registered in component registry: {service_name}", "", "services"
                    )
        except Exception as e:
            self.add_issue(
                "integration", "low", str(service_file), 0,
                f"Could not analyze service: {e}", "", "services"
            )
    
    def check_api_integration(self, route_file: Path):
        """Check if API route is properly integrated."""
        try:
            with open(route_file, 'r') as f:
                content = f.read()
            
            # Check for proper error handling
            if 'HTTPException' not in content and '@app.' in content:
                self.add_issue(
                    "api_endpoints", "medium", str(route_file), 0,
                    "API endpoint may lack proper error handling", "", "api"
                )
            
            # Check for Pydantic models
            if 'BaseModel' not in content and 'router.post(' in content:
                self.add_issue(
                    "api_endpoints", "medium", str(route_file), 0,
                    "API endpoint may lack request/response models", "", "api"
                )
        except Exception as e:
            self.add_issue(
                "api_endpoints", "low", str(route_file), 0,
                f"Could not analyze API route: {e}", "", "api"
            )
    
    def validate_configuration_file(self, config_path: Path):
        """Validate a configuration file."""
        try:
            if config_path.suffix == '.json':
                with open(config_path, 'r') as f:
                    json.load(f)
            elif config_path.suffix in ['.yaml', '.yml']:
                import yaml
                with open(config_path, 'r') as f:
                    yaml.safe_load(f)
        except Exception as e:
            self.add_issue(
                "configuration", "high", str(config_path), 0,
                f"Configuration file invalid: {e}", "", "config"
            )
    
    def check_endpoint_implementation(self, endpoint_file: Path):
        """Check if API endpoint is properly implemented."""
        try:
            with open(endpoint_file, 'r') as f:
                content = f.read()
            
            # Check for actual implementation vs stub
            if len(content.strip()) < 100:
                self.add_issue(
                    "api_endpoints", "medium", str(endpoint_file), 0,
                    "API endpoint file appears to be minimal or incomplete", "", "api"
                )
            
            # Check for actual route definitions
            if '@router.' not in content and '@app.' not in content:
                self.add_issue(
                    "api_endpoints", "high", str(endpoint_file), 0,
                    "API endpoint file lacks route definitions", "", "api"
                )
        except Exception as e:
            self.add_issue(
                "api_endpoints", "low", str(endpoint_file), 0,
                f"Could not analyze endpoint: {e}", "", "api"
            )
    
    def add_issue(self, category: str, severity: str, file_path: str, line_number: int, 
                  description: str, code_snippet: str, component: str):
        """Add an issue to the audit results."""
        issue = AuditIssue(
            category=category,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            description=description,
            code_snippet=code_snippet,
            component=component
        )
        self.issues.append(issue)
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive audit report."""
        print("\n📊 Generating Comprehensive Report...")
        
        # Categorize issues
        issues_by_category = {}
        issues_by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        
        for issue in self.issues:
            # By category
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)
            
            # By severity
            issues_by_severity[issue.severity].append(issue)
        
        # Component status
        component_status = {}
        for issue in self.issues:
            if issue.component not in component_status:
                component_status[issue.component] = {'issues': [], 'status': 'unknown'}
            component_status[issue.component]['issues'].append(issue)
            
            # Determine overall status based on severity
            if issue.severity == 'critical':
                component_status[issue.component]['status'] = 'critical'
            elif issue.severity == 'high' and component_status[issue.component]['status'] != 'critical':
                component_status[issue.component]['status'] = 'warning'
            elif issue.severity == 'medium' and component_status[issue.component]['status'] == 'unknown':
                component_status[issue.component]['status'] = 'notice'
        
        # Generate summary statistics
        total_issues = len(self.issues)
        critical_count = len(issues_by_severity['critical'])
        high_count = len(issues_by_severity['high'])
        medium_count = len(issues_by_severity['medium'])
        low_count = len(issues_by_severity['low'])
        
        # Generate recommendations
        recommendations = self.generate_recommendations(issues_by_severity, issues_by_category)
        
        return {
            'audit_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_files_scanned': len(list(self.project_root.rglob("*.py"))),
                'total_issues_found': total_issues,
                'severity_distribution': {
                    'critical': critical_count,
                    'high': high_count,
                    'medium': medium_count,
                    'low': low_count
                }
            },
            'executive_summary': {
                'overall_health': self.calculate_overall_health(critical_count, high_count, medium_count, low_count),
                'priority_focus_areas': self.get_priority_areas(issues_by_severity),
                'completion_estimate': self.estimate_completion(issues_by_category)
            },
            'detailed_findings': {
                'issues_by_category': {
                    cat: [{'severity': i.severity, 'file': i.file_path, 'line': i.line_number, 
                           'description': i.description, 'snippet': i.code_snippet} 
                           for i in issues] 
                    for cat, issues in issues_by_category.items()
                },
                'issues_by_severity': {
                    sev: [{'category': i.category, 'file': i.file_path, 'line': i.line_number,
                          'description': i.description, 'snippet': i.code_snippet}
                         for i in issues]
                    for sev, issues in issues_by_severity.items()
                },
                'component_status': component_status
            },
            'integration_gaps': self.identify_integration_gaps(issues_by_category),
            'missing_implementations': self.identify_missing_implementations(issues_by_category),
            'configuration_issues': issues_by_category.get('configuration', []),
            'api_endpoint_issues': issues_by_category.get('api_endpoints', []),
            'testing_gaps': issues_by_category.get('testing', []),
            'recommendations': recommendations,
            'next_steps': self.generate_next_steps(issues_by_severity)
        }
    
    def calculate_overall_health(self, critical: int, high: int, medium: int, low: int) -> str:
        """Calculate overall project health score."""
        total = critical + high + medium + low
        if total == 0:
            return "excellent"
        
        critical_weight = 10
        high_weight = 5
        medium_weight = 2
        low_weight = 1
        
        weighted_score = (critical * critical_weight + high * high_weight + 
                        medium * medium_weight + low * low_weight)
        
        if critical > 0:
            return "critical"
        elif weighted_score > 20:
            return "poor"
        elif weighted_score > 10:
            return "fair"
        elif weighted_score > 5:
            return "good"
        else:
            return "excellent"
    
    def get_priority_areas(self, issues_by_severity: Dict) -> List[str]:
        """Get priority areas based on critical and high issues."""
        priority_areas = []
        
        for issue in issues_by_severity['critical'] + issues_by_severity['high']:
            if issue.category not in priority_areas:
                priority_areas.append(issue.category)
        
        return priority_areas
    
    def estimate_completion(self, issues_by_category: Dict) -> float:
        """Estimate project completion percentage."""
        total_issues = sum(len(issues) for issues in issues_by_category.values())
        
        # Weight different categories differently
        category_weights = {
            'core_components': 3,
            'api_endpoints': 3,
            'integration': 2,
            'configuration': 2,
            'implementation': 1,
            'testing': 1,
            'database': 1,
            'frontend_integration': 2
        }
        
        weighted_issues = 0
        max_weight = sum(category_weights.values())
        
        for category, issues in issues_by_category.items():
            weight = category_weights.get(category, 1)
            weighted_issues += len(issues) * weight
        
        # Estimate completion (inverse of issues)
        completion = max(0, 100 - (weighted_issues / (max_weight * 10)) * 100)
        return round(completion, 1)
    
    def identify_integration_gaps(self, issues_by_category: Dict) -> List[Dict]:
        """Identify specific integration gaps."""
        integration_issues = issues_by_category.get('integration', [])
        return [
            {
                'type': 'service_gap',
                'description': issue.description,
                'file': issue.file_path,
                'severity': issue.severity
            }
            for issue in integration_issues
        ]
    
    def identify_missing_implementations(self, issues_by_category: Dict) -> List[Dict]:
        """Identify missing implementations."""
        impl_issues = issues_by_category.get('implementation', [])
        return [
            {
                'type': 'missing_impl',
                'description': issue.description,
                'file': issue.file_path,
                'line': issue.line_number,
                'snippet': issue.code_snippet,
                'severity': issue.severity
            }
            for issue in impl_issues
        ]
    
    def generate_recommendations(self, issues_by_severity: Dict, issues_by_category: Dict) -> List[Dict]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Critical issues first
        if issues_by_severity['critical']:
            recommendations.append({
                'priority': 'immediate',
                'category': 'critical',
                'title': 'Address Critical Issues Immediately',
                'description': f"Resolve {len(issues_by_severity['critical'])} critical issues that block system functionality",
                'estimated_effort': 'high'
            })
        
        # High priority issues
        if issues_by_severity['high']:
            recommendations.append({
                'priority': 'high',
                'category': 'high',
                'title': 'Resolve High Priority Issues',
                'description': f"Address {len(issues_by_severity['high'])} high-priority issues affecting system quality",
                'estimated_effort': 'medium'
            })
        
        # Service integrations
        if 'integration' in issues_by_category:
            recommendations.append({
                'priority': 'high',
                'category': 'integration',
                'title': 'Complete Service Integrations',
                'description': f"Complete {len(issues_by_category['integration'])} service integrations",
                'estimated_effort': 'medium'
            })
        
        # API endpoints
        if 'api_endpoints' in issues_by_category:
            recommendations.append({
                'priority': 'medium',
                'category': 'api',
                'title': 'Finalize API Endpoints',
                'description': f"Complete {len(issues_by_category['api_endpoints'])} API endpoint implementations",
                'estimated_effort': 'medium'
            })
        
        # Testing
        if 'testing' in issues_by_category:
            recommendations.append({
                'priority': 'medium',
                'category': 'testing',
                'title': 'Improve Test Coverage',
                'description': f"Add missing tests for {len(issues_by_category['testing'])} components",
                'estimated_effort': 'low'
            })
        
        return recommendations
    
    def generate_next_steps(self, issues_by_severity: Dict) -> List[str]:
        """Generate specific next steps."""
        steps = []
        
        # Immediate actions
        if issues_by_severity['critical']:
            steps.append("1. Fix all NotImplementedError exceptions in core components")
            steps.append("2. Complete missing critical component implementations")
        
        if issues_by_severity['high']:
            steps.append("3. Replace all placeholder service implementations")
            steps.append("4. Complete API endpoint error handling")
        
        steps.append("5. Set up comprehensive integration testing")
        steps.append("6. Document all API endpoints with OpenAPI/Swagger")
        steps.append("7. Complete frontend-backend API integration")
        steps.append("8. Implement proper database schemas and migrations")
        
        return steps

async def main():
    """Main function to run the audit."""
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    auditor = ComprehensiveAuditor(project_root)
    report = await auditor.run_full_audit()
    
    # Save report
    report_file = Path(project_root) / f"COMPREHENSIVE_AUDIT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n🎯 AUDIT COMPLETE!")
    print(f"📄 Report saved to: {report_file}")
    print(f"\n📊 SUMMARY:")
    print(f"   Total Issues: {report['audit_metadata']['total_issues_found']}")
    print(f"   Critical: {report['audit_metadata']['severity_distribution']['critical']}")
    print(f"   High: {report['audit_metadata']['severity_distribution']['high']}")
    print(f"   Medium: {report['audit_metadata']['severity_distribution']['medium']}")
    print(f"   Low: {report['audit_metadata']['severity_distribution']['low']}")
    print(f"   Overall Health: {report['executive_summary']['overall_health']}")
    print(f"   Completion Estimate: {report['executive_summary']['completion_estimate']}%")
    
    if report['executive_summary']['priority_focus_areas']:
        print(f"\n🎯 Priority Areas: {', '.join(report['executive_summary']['priority_focus_areas'])}")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())