"""
Angela AI v6.0 - Integration Tests Package
整合测试包

This package contains comprehensive integration tests for Angela AI v6.0,
verifying all system components work together correctly.

测试模块：
- test_full_system_integration.py: 完整系统整合测试
- test_end_to_end_scenarios.py: 端到端场景测试
- test_performance_benchmarks.py: 性能基准测试
- test_error_recovery.py: 错误恢复测试
- test_digital_life_compliance.py: 数字生命合规测试
- run_integration_tests.py: 测试运行器

Usage:
    # 运行所有测试
    python run_integration_tests.py
    
    # 运行完整测试套件（包括慢测试）
    python run_integration_tests.py --full
    
    # 只运行快速测试
    python run_integration_tests.py --quick
    
    # 生成HTML报告
    python run_integration_tests.py --report
    
    # 列出所有测试文件
    python run_integration_tests.py --list
    
    # 使用pytest直接运行
    pytest tests/integration/ -v
    
    # 运行特定测试类别
    pytest tests/integration/test_full_system_integration.py -v -m system_integration
    pytest tests/integration/test_end_to_end_scenarios.py -v -m e2e
    pytest tests/integration/test_performance_benchmarks.py -v -m performance

Markers:
    - integration: 所有整合测试
    - system_integration: 系统整合测试
    - e2e: 端到端测试
    - performance: 性能测试
    - slow: 慢测试（长时间运行）
    - flaky: 不稳定测试

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

__version__ = '6.0.0'
__author__ = 'Angela AI Development Team'
