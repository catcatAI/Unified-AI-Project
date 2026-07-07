# Active Scripts Reference

This document lists the **currently active and recommended** scripts for the Unified-AI-Project.

## Core Operations

### Backend Management
- **`restart_backend.ps1`**: Restart the FastAPI backend server
- **`start_backend.bat`**: Start backend in development mode
- **`start_all.bat`**: Start both backend and frontend concurrently

### Health & Monitoring
- **`check_auth_status.py`**: Check authentication status
- **`check_last_memories.py`**: Inspect recent HAM memory entries
- **`check_vec_store.py`**: Verify vector store integrity
- **`debug_memory.py`**: Debug memory system issues
- **`check_ports.ps1`**: Check port availability

### Google Drive Integration
- **`trigger_sync.py`**: Manually trigger Drive file synchronization
- **`verify_drive_analyzer.py`**: Verify Drive Analyzer functionality
- **`get_drive_auth_url.py`**: Generate OAuth authorization URL
- **`exchange_drive_code.py`**: Exchange auth code for tokens
- **`clear_drive_sync.py`**: Reset Drive sync state

### Training & AI
- **`train_ed3n.py`**: ED3N training
- **`train_pipeline.py`**: Training pipeline
- **`train_visual_decoder.py`**: Train VisualDecoder texture weights via FullTrainingPipeline (Phase 1+2+3a). Saves `data/multimodal/weights/p29_trained.npz` with 7 weight arrays. Usage: `python scripts/train_visual_decoder.py --texture-steps 200`
- **`train_multimodal_real.py`**: Full multimodal training with real CIFAR-10 + ESC-50 data. Phase 1+2 (real contrastive + reconstruction) + Phase 3a (texture) + Phase 3b (wavetable). Saves joint `p29_trained.npz` (15 arrays). Usage: `python scripts/train_multimodal_real.py --texture-steps 500`
- **`generate_training_data.py`**: Generate training data

### Development & Testing
- **`verify_ice_loop.py`**: Verify ICE (Ingest-Cognition-Execution) loop
- **`verify_phase_2_loop.py`**: Verify Phase 2 quality-based reward loop
### Project Management
- **`unified-ai.bat`**: Main project launcher (comprehensive)
- **`unified-ai-cli.bat`**: CLI interface for project operations
- **`setup_project.bat`**: Initial project setup (Windows)
- **`setup_project.sh`**: Initial project setup (Linux/Mac)
- **`update-docs.bat`**: Update documentation (Windows)
- **`update-docs.ps1`**: Update documentation (PowerShell)

### Utilities
- **`run_angela.py`**: Primary launcher
- **`_run_phase1.bat`**: Phase 1 launcher
- **`ai-runner.bat`**: AI runner
- **`analyze_roadmap_from_logs.py`**: Extract roadmap from logs
- **`ingest_my_activities.py`**: Ingest user activities into memory
- **`filter_files.ps1`**: File filtering

## scripts/utils/

- **`init_config.py`**: Configuration initialization
- **`health_check.py`**: Comprehensive health check
- **`check_resources.py`**: System resource monitor
- **`verify_p0_systems.py`**: P0 systems verification
- **`improve_live2d_loading.py`**: Live2D loading optimization
- **`api_test_report.py`**: Generate API test reports
- **`enable_commented_tests.py`**: Enable commented-out tests
- **`automated_integration_test_pipeline.py`**: Automated integration test pipeline
- **`check_test_collection.py`**: Verify test collection
- **`check_test_results.py`**: Check test results from runs
- **`continuous_test_improvement.py`**: Continuous improvement of test suite
- **`deadlock_detector.py`**: Detect deadlocks in async tests
- **`enterprise_test_suite.py`**: Enterprise-scale test suite runner
- **`extract_latest_failures.py`**: Extract latest test failures
- **`find_skipped_tests.py`**: Find all skipped tests
- **`generate_test_report.py`**: Generate test reports
- **`intelligent_test_generator.py`**: AI-driven test generation
- **`maintain_test_suite.py`**: Test suite maintenance tools
- **`optimize_test_suite.py`**: Test suite optimization
- **`process_test_results.py`**: Process and analyze test results
- **`project_function_test_mapping.py`**: Map tests to project functions
- **`run_integration_tests.py`**: Run integration tests
- **`run_test_direct.py`**: Run tests directly
- **`run_test_subprocess.py`**: Run tests in subprocess
- **`run_tests_with_compat.py`**: Run tests with compatibility mode
- **`smart_test_runner.py`**: Smart test runner with analytics
- **`_run_pc_tests.py`**: Private PC test runner
- **`_run_pc_tests_file.py`**: Private PC test file runner

## tools/

### Legacy Scripts
- **`install_angela.py`**: Full installer
- **`AngelaLauncher.bat`**: Windows launcher with auto-repair

## Usage Guidelines

### Quick Start
```powershell
# Start the entire system
.\scripts\start_all.bat

# Or use the comprehensive launcher
.\scripts\unified-ai.bat
```

### Health Check
```powershell
# Quick check
python scripts/check_auth_status.py

# Full diagnostics
python scripts/utils/health_check.py

# Port availability
.\scripts\check_ports.ps1
```

### Drive Operations
```powershell
# Trigger manual sync
python scripts/trigger_sync.py

# Verify analyzer
python scripts/verify_drive_analyzer.py
```

## Maintenance Notes

- **Active Scripts**: ~30 scripts in `scripts/` directory
- **Utilities**: 28 scripts in `scripts/utils/` (was 5 — expanded with test utility scripts from `tests/utils/`)
- **Tools**: 2 scripts in `tools/`
- **Tests/utils remaining**: `test_text_utils.py`, `text_utils.py` (legitimate test files with pytest test functions)
- **Last Cleanup**: 2026-07-07
