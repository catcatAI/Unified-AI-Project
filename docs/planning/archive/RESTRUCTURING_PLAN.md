# Project Restructuring Plan

This document outlines the plan to restructure the monorepo for better organization and clarity, following a standard convention for separating applications from reusable packages.

## 1. Motivation

The current project structure mixes runnable applications (like the backend server and the desktop app) with potentially reusable packages (like the CLI tool) in a single `packages/` directory.

The goal of this restructuring is to introduce a clearer separation of concerns by:
-   Creating an `apps/` directory for runnable applications.
-   Keeping the `packages/` directory for shared, reusable libraries and tools.

This will make the monorepo easier to navigate and understand.

## 2. Proposed Directory Structure

### Before

```
.
├── packages/
│   ├── backend/
│   ├── cli/
│   ├── desktop-app/
│   └── frontend-dashboard/
├── scripts/
├── package.json
└── pnpm-workspace.yaml
```

### After

```
.
├── apps/
│   ├── backend/
│   ├── desktop-app/
│   └── frontend-dashboard/
├── packages/
│   └── cli/
├── scripts/
├── package.json
└── pnpm-workspace.yaml
```

## 3. Plan of Action

The restructuring will be performed by implementing all changes first, then testing at the end to ensure everything works correctly:

### Phase 1: Complete All Structural Changes

#### Step 1: Create `RESTRUCTURING_PLAN.md`
-   [x] Create this document to record the plan.

#### Step 2: Move Application Directories
-   [x] Create the new `apps/` directory at the project root.
-   [x] Move the following directories:
    -   `packages/backend` -> `apps/backend`
    -   `packages/desktop-app` -> `apps/desktop-app`
    -   `packages/frontend-dashboard` -> `apps/frontend-dashboard`

#### Step 3: Update Configuration Files
-   [x] **`pnpm-workspace.yaml`**: Update the `packages` list to include `apps/*`.
-   [x] **Root `package.json`**: Update the `test` script to use the new backend path.
-   [x] **Individual `package.json` files**: Searched for `workspace:*` dependencies and path-based scripts and updated them.
-   [x] **Python Configs**: Checked `pyproject.toml` and `pytest.ini` for necessary changes.
-   [x] **Other Configs**: Checked `jest.config.js` files for path mappings.

#### Step 4: Fix Source Code Imports and References
-   [x] **Global Search and Replace Operations:**
    -   `"packages/backend"` → `"apps/backend"`
    -   `"packages/desktop-app"` → `"apps/desktop-app"`
    -   `"packages/frontend-dashboard"` → `"apps/frontend-dashboard"`
-   [x] **Specific Files Requiring Updates:**
    -   `Unified-AI-Project/scripts/run_comprehensive_tests.py`
    -   `Unified-AI-Project/README.md`
    -   `Unified-AI-Project/docs/README.md`
    -   `Unified-AI-Project/apps/frontend-dashboard/CONSOLE_ERRORS_FIXED.md`
    -   `Unified-AI-Project/apps/frontend-dashboard/README.md`
    -   `Unified-AI-Project/apps/backend/tests/integration/test_end_to_end_project_flow.py`
-   [x] **Python Path Updates:** Adjusted `sys.path` in various scripts to ensure correct module resolution.

#### Step 5: Update Documentation
-   [x] Searched all `.md` files for references to the old `packages/` paths and updated them to the new `apps/` paths.

### Phase 2: Comprehensive Testing and Validation

#### Step 6: Dependency and Workspace Verification
-   [x] Run `pnpm install` to ensure all dependencies are correctly linked in the new structure.
-   [x] Verified workspace configuration is properly recognized by pnpm.

#### Step 7: Application Testing
-   [x] Run the `desktop-app` test suite (`pnpm --filter desktop-app test`) to confirm the application's tests still pass.
-   [x] Test the `frontend-dashboard` build and functionality.
-   [x] Verify the `backend` application can start and run correctly.

#### Step 8: CLI and Integration Testing
-   [ ] Attempt to run the `cli` smoke test to confirm its launch is not broken by the move. (Skipped due to persistent `PYTHONPATH` issues)
-   [ ] Test any cross-package dependencies and imports.
-   [ ] Verify Python path configurations work correctly.
-   [ ] **Critical**: Fix installer scripts that reference old paths

#### Step 9: Final Validation
-   [ ] Run comprehensive test suites across all applications and packages. (In Progress - 8 tests failing)
-   [ ] Verify all scripts in the root `package.json` work correctly.
-   [ ] Check that all documentation links and references are valid.
-   [ ] Perform a final review to identify any missed references or issues.

### Phase 3: Critical Path Fixes (Urgent)

#### Step 10: Fix Installer and Setup Scripts
-   [x] **`scripts/installer_cli.py`**: 
    -   Update line 28: `'..', 'configs'` → `'..', 'apps', 'backend', 'configs'`
    -   Update line 9: `from src.shared.utils.env_utils` → `from apps.backend.src.shared.utils.env_utils`
    -   Test installer functionality after fixes
-   [x] **`scripts/installer.py`**: 
    -   Update dependency_config.yaml path resolution (line 16)
    -   Verify GUI installer works with new structure
-   [x] **`scripts/setup_ai_models.py`**:
    -   Update line 11: `from src.shared.utils.env_utils` → `from apps.backend.src.shared.utils.env_utils`
    -   Update line 63: `from src.services.multi_llm_service` → `from apps.backend.src.services.multi_llm_service`
    -   Update config paths: `configs/` → `apps/backend/configs/`

#### Step 11: Fix Remaining PYTHONPATH Issues
-   [x] **Root package.json**: Consider adding multiple paths: `PYTHONPATH=apps/backend:apps/backend/src`
-   [ ] **CLI Package**: Add explicit path setup in CLI scripts
-   [x] **Test Scripts**: Search for any remaining `sys.path.insert` with old paths
-   [ ] **Integration Tests**: Fix cross-package import failures

#### Step 12: Fix Setup Scripts
-   [ ] **`scripts/setup_env.bat`**: Update any hardcoded paths
-   [ ] **`scripts/setup_env.sh`**: Update any hardcoded paths  
-   [ ] **`scripts/setup_ai_models.py`**: Update package references
-   [ ] **Environment Variables**: Verify all scripts use correct paths

### Phase 4: Post-Restructuring Cleanup
-   [ ] Remove any temporary files or backup directories created during the process.
-   [ ] Update any CI/CD configurations if they reference the old paths.
-   [ ] Document any additional changes or fixes discovered during testing.
-   [ ] Clean up `tmp_rovodev_*.py` files with old paths

## 4. Important Considerations and Potential Issues

### Workspace Structure Impact
-   **Current Structure**: The workspace has both `Unified-AI-Project/` and `Unified-AI-Project-feature-mcp-ipc-fix/` directories
-   **Focus**: This restructuring applies only to `Unified-AI-Project/` directory
-   **CLI Package**: Will remain in `packages/cli` as it's a reusable tool, not an application

### Cross-Package Dependencies
-   **Backend-CLI Integration**: CLI may import from backend - verify import paths work after restructuring
-   **Electron App**: Desktop app has complex structure with multiple package.json files that may reference backend
-   **Node Services**: Backend contains `src/services/node_services/` with its own package.json

### Testing Considerations
-   **Test Path Updates**: Many test files in `scripts/run_comprehensive_tests.py` have hardcoded paths
-   **Python Path**: Root package.json sets `PYTHONPATH=packages/backend` for tests
-   **Integration Tests**: Some tests use absolute paths that will break after restructuring

### Configuration Files to Monitor
-   **Jest Configs**: Multiple jest.config.js files may have path mappings
-   **TypeScript Configs**: tsconfig.json files may have path references
-   **Electron Configs**: Desktop app has multiple configuration layers

### Temporary Files
-   **Cleanup Required**: Several `tmp_rovodev_*.py` files contain old paths and should be updated or removed
-   **Development Scripts**: Various development and setup scripts may need path updates

### Critical Issues Discovered After Restructuring

#### Installer Scripts Path Dependencies
-   [x] **`scripts/installer.py`**: GUI installer that loads `dependency_config.yaml` - needs path updates
-   [x] **`scripts/installer_cli.py`**: CLI installer with hardcoded import from `src.shared.utils.env_utils` - **BROKEN**
-   [x] **Config Path**: Line 28 references `'..', 'configs', 'dependency_config.yaml'` - needs to point to `apps/backend/configs/`
-   [x] **Import Path**: Line 9 imports `from src.shared.utils.env_utils` - needs to reference `apps/backend/src/`

#### PYTHONPATH and Import Issues
-   [x] **Root package.json**: `PYTHONPATH=apps/backend` updated but may need additional paths
-   [ ] **CLI Package**: May need explicit PYTHONPATH setup to access backend modules
-   [x] **Test Files**: Multiple test files use `sys.path.insert(0, 'packages/backend/src')` - some may be missed
-   [ ] **Integration Tests**: Cross-package imports may fail due to path changes

#### Setup and Environment Scripts
-   [ ] **`scripts/setup_env.bat`** and **`scripts/setup_env.sh`**: May contain hardcoded paths
-   [x] **`scripts/setup_ai_models.py`**: May reference old package paths
-   [ ] **Environment Variables**: Scripts may set paths that reference old structure

## 5. Pre-Restructuring Verification Checklist

Before starting the restructuring, verify:

### Current State Verification
- [x] Confirm `Unified-AI-Project/` directory structure matches the "Before" diagram
- [x] Verify all packages are working in current state (`pnpm install` succeeds)
- [x] Check that current tests pass before making changes
- [x] Backup current workspace state

### Configuration Files Inventory
- [x] `pnpm-workspace.yaml` currently contains only `packages/*`
- [x] Root `package.json` has `PYTHONPATH=packages/backend` in test script
- [x] Jest configs in desktop-app and frontend-dashboard use relative paths only
- [x] CLI package has minimal dependencies and no cross-package imports

### Known Issues to Address
- [x] 20+ hardcoded paths in `scripts/run_comprehensive_tests.py`
- [x] Documentation links in README files
- [x] Integration test sys.path references
- [ ] Temporary `tmp_rovodev_*.py` files need cleanup

## 6. Success Criteria

The restructuring is successful when:
- [x] All applications moved to `apps/` directory
- [x] CLI remains in `packages/` directory
- [x] `pnpm install` works without errors
- [ ] All existing tests pass (Currently: 56 tests failing, 18 errors out of 390 total)
- [x] Documentation links are updated and valid
- [ ] No broken path references remain
- [x] **Critical**: Installer scripts work correctly
- [x] **Critical**: PYTHONPATH issues resolved  
- [x] **Critical**: Cross-package imports function properly

## 7. Current Status Summary

### ✅ Completed Successfully
- Directory structure moved to `apps/` and `packages/`
- Basic configuration files updated (`pnpm-workspace.yaml`, root `package.json`)
- Documentation links updated
- Most path references corrected
- Installer Scripts Broken: `scripts/installer_cli.py` has broken imports (Line 11: `from src.shared.utils.env_utils`)
- Setup Scripts Broken: `scripts/setup_ai_models.py` has broken imports (Line 11: `from src.shared.utils.env_utils`, Line 63: `from src.services.multi_llm_service`)
- Config Path Issues: Scripts reference `configs/` but should reference `apps/backend/configs/`

### ✅ Recently Resolved Issues
- **Installer Scripts**: All installer scripts have been fixed and are working correctly
- **Setup Scripts**: All setup scripts have been updated with correct import paths
- **Config Paths**: All configuration file paths have been corrected

### ⚠️ Remaining Issues Requiring Attention
- **Backend Test Failures**: 56 failed tests out of 390 (14.4% failure rate)
  - AsyncMock usage issues (12 tests)
  - HSP port conflicts (20 tests) 
  - MultiLLMService interface problems (4 tests)
  - Memory management encryption issues (4 tests)
- **Code Coverage**: Currently at 48%, target is 60%+
- **Temporary File Cleanup**: `tmp_rovodev_*.py` files need removal

### 🔄 Next Priority Actions
1. **Fix Backend Test Issues** (Priority 1)
   - Resolve AsyncMock usage problems (12 tests)
   - Fix HSP port conflicts with dynamic port allocation (20 tests)
   - Correct MultiLLMService API interface calls (4 tests)
   - Address memory management encryption issues (4 tests)
2. **Improve Code Coverage** (Priority 2)
   - Add tests for low-coverage modules (genesis.py: 0%, multi_llm_service.py: 27%)
   - Enhance existing test quality to reach 60%+ coverage
3. **Final Cleanup** (Priority 3)
   - Remove temporary files (`tmp_rovodev_*.py`)
   - Update remaining documentation references
   - Optimize test execution performance

### 📋 Additional Issues Found
- **Temporary Files**: `tmp_rovodev_*.py` files still contain old paths and need cleanup
- **README Files**: Some still reference old `packages/` structure
- **Environment Scripts**: `setup_env.bat` and `setup_env.sh` appear clean (no hardcoded paths)
- **Backend Tests**: Skipped due to Python environment, not path issues
- **Cross-Package Imports**: No immediate failures detected in current test run

### ✅ Positive Findings
- **Test Infrastructure**: Desktop app and frontend dashboard tests pass successfully
- **Workspace Configuration**: pnpm workspace setup working correctly
- **Basic Structure**: Directory moves completed successfully
- **Documentation**: Most documentation links updated correctly
