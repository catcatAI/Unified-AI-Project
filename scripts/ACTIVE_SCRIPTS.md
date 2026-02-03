# Active Scripts Reference

This document lists the **currently active and recommended** scripts for the Unified-AI-Project.

## Core Operations

### Backend Management
- **`restart_backend.ps1`**: Restart the FastAPI backend server
- **`start_backend.bat`**: Start backend in development mode
- **`start_all.bat`**: Start both backend and frontend concurrently

### Health & Monitoring
- **`simple_health_check.py`**: Quick API health verification
- **`check_system_health.py`**: Comprehensive system diagnostics
- **`port_manager.js`**: Manage port allocations and conflicts

### Google Drive Integration
- **`trigger_sync.py`**: Manually trigger Drive file synchronization
- **`verify_drive_analyzer.py`**: Verify Drive Analyzer functionality
- **`get_drive_auth_url.py`**: Generate OAuth authorization URL
- **`exchange_drive_code.py`**: Exchange auth code for tokens
- **`clear_drive_sync.py`**: Reset Drive sync state

### Memory & Data
- **`check_last_memories.py`**: Inspect recent HAM memory entries
- **`check_vec_store.py`**: Verify vector store integrity
- **`debug_memory.py`**: Debug memory system issues
- **`wipe_memory.py`**: Clear all memory (use with caution)

### Development & Testing
- **`verify_ice_loop.py`**: Verify ICE (Ingest-Cognition-Execution) loop
- **`verify_phase_2_loop.py`**: Verify Phase 2 quality-based reward loop
- **`test_drive_integration.py`**: Test Drive integration end-to-end
- **`test_proactive_messaging.py`**: Test proactive messaging system

### Project Management
- **`unified-ai.bat`**: Main project launcher (comprehensive)
- **`unified-ai-cli.bat`**: CLI interface for project operations
- **`start-unified-ai.bat`**: Quick start script
- **`setup_project.bat`**: Initial project setup
- **`update-docs.bat`**: Update documentation
- **`update-docs.ps1`**: PowerShell version of doc updater

### Utilities
- **`check_ports.ps1`**: Check port availability
- **`analyze_roadmap_from_logs.py`**: Extract roadmap from logs
- **`ingest_my_activities.py`**: Ingest user activities into memory

## Archived Scripts

The following categories of scripts have been moved to `archive/legacy_scripts/`:

### Cleanup & Recovery (Obsolete)
- `cleanup_backup_dirs.ps1`
- `cleanup_backup_modules.ps1`
- `recover_all_deleted_files.ps1`
- `restore_deleted_files.ps1` (and v2, v3, v4)

### Testing (Replaced by pytest)
- `run_check.bat`
- `run_integration.bat`
- `run_test.bat`
- `move_scattered_tests.bat`

### Legacy Architecture
- `setup-wsl2.sh` (Ray distributed setup, no longer needed)

### Root Directory (Migrated)
- `test_import.py`, `test_import2.py` (moved to archive)
- `test_curl.py`, `debug_math.py`, `patch_api.py` (moved to archive)

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
python scripts/simple_health_check.py

# Full diagnostics
python scripts/check_system_health.py
```

### Drive Operations
```powershell
# Trigger manual sync
python scripts/trigger_sync.py

# Verify analyzer
python scripts/verify_drive_analyzer.py
```

## Maintenance Notes

- **Active Scripts**: 30 scripts in `scripts/` directory
- **Archived Scripts**: 14+ scripts in `archive/legacy_scripts/`
- **Last Cleanup**: 2026-01-25 (Phase 7.3)
- **Recommendation**: Use `unified-ai.bat` for most operations
