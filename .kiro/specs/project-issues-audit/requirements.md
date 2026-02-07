# Angela AI Project Issues Audit - Requirements

## 1. Overview

This spec documents critical issues found in the Angela AI project that need to be addressed to ensure the project is production-ready and matches its documentation claims.

## 2. User Stories

### 2.1 As a Developer
**I want** the project documentation to accurately reflect the actual codebase structure  
**So that** I can successfully set up and contribute to the project without confusion

### 2.2 As a User
**I want** all referenced files and resources to exist  
**So that** I can follow the installation instructions without encountering missing file errors

### 2.3 As a Project Maintainer
**I want** proper licensing and legal documentation  
**So that** the project complies with open-source standards and protects contributors

### 2.4 As a Developer
**I want** consistent version information across all documentation  
**So that** I know which version I'm working with

## 3. Acceptance Criteria

### 3.1 Documentation Accuracy Issues

**AC 3.1.1**: README.md git clone command must be valid
- **Current State**: Line 158 contains malformed git clone command: `git clone https://github.com/catcatAI/# Unified AI Project (Angela) - v6.2.0`
- **Expected**: Should be `git clone https://github.com/catcatAI/Unified-AI-Project.git`
- **Priority**: CRITICAL
- **Impact**: Users cannot clone the repository using the provided command

**AC 3.1.2**: All referenced documentation files must exist
- **Current State**: README references `CROSS_PLATFORM_TESTING.md` which exists in two locations (root and docs/)
- **Expected**: Single source of truth, preferably in docs/ with clear reference
- **Priority**: MEDIUM
- **Impact**: Potential confusion about which file is authoritative

**AC 3.1.3**: Module count in README must match actual implementation
- **Current State**: README claims "22 JavaScript modules" in desktop app
- **Actual Count**: 40 JavaScript files found in `apps/desktop-app/electron_app/js/`
- **Expected**: Documentation should reflect actual count or clarify what constitutes a "module"
- **Priority**: LOW
- **Impact**: Minor documentation inaccuracy

### 3.2 Missing Critical Files

**AC 3.2.1**: LICENSE file must exist in project root
- **Current State**: No LICENSE file found in project root
- **Expected**: MIT License file as claimed in README badges and documentation
- **Priority**: CRITICAL
- **Impact**: Legal compliance issue, unclear licensing terms

**AC 3.2.2**: Prebuilt installers referenced in README must exist or be clearly marked as unavailable
- **Current State**: README mentions `AngelaAI-Setup.exe`, `AngelaAI.dmg`, `AngelaAI.AppImage`
- **Expected**: Either provide these files or clearly mark as "Coming Soon" or "Build from Source Only"
- **Priority**: HIGH
- **Impact**: User confusion, broken installation path

**AC 3.2.3**: AngelaLauncher.bat must exist in project root
- **Current State**: File exists in root directory
- **Expected**: ✅ PASS
- **Priority**: N/A
- **Impact**: None

### 3.3 Version Inconsistencies

**AC 3.3.1**: Version numbers must be consistent across all documentation
- **Current State**: 
  - README title: "v6.2.0"
  - README footer: "Version: 6.1.0"
  - README footer: "Release Date: 2026-02-05"
  - README last updated: "2026-02-07"
- **Expected**: Single consistent version number throughout
- **Priority**: MEDIUM
- **Impact**: Confusion about actual project version

**AC 3.3.2**: Phase/Status information must be consistent
- **Current State**: 
  - "Phase 14 Complete" in some places
  - "Phase 12 Restoration Complete" in others
  - "99.2%" and "99%" completion percentages
- **Expected**: Consistent phase and completion status
- **Priority**: LOW
- **Impact**: Minor confusion about project status

### 3.4 Repository URL Issues

**AC 3.4.1**: All GitHub URLs must be valid and consistent
- **Current State**: Multiple references to `https://github.com/catcatAI/Unified-AI-Project`
- **Expected**: Verify this is the correct repository URL or update to actual URL
- **Priority**: HIGH
- **Impact**: Users cannot access repository, issues, or documentation

### 3.5 Project Structure Documentation

**AC 3.5.1**: Project structure in README must match actual directory structure
- **Current State**: README shows detailed structure but some paths may be outdated
- **Expected**: Verify all paths in "Project Structure" section match reality
- **Priority**: MEDIUM
- **Impact**: Developer confusion when navigating codebase

**AC 3.5.2**: Native modules documentation must be accurate
- **Current State**: README documents 3 native audio modules (WASAPI, CoreAudio, PulseAudio)
- **Actual State**: All 3 directories exist in `apps/desktop-app/native_modules/`
- **Expected**: ✅ PASS
- **Priority**: N/A
- **Impact**: None

### 3.6 Configuration and Setup Issues

**AC 3.6.1**: All referenced configuration files must exist or be documented as optional
- **Current State**: README mentions `config/angela_config.yaml`
- **Expected**: Verify file exists or document as auto-generated
- **Priority**: MEDIUM
- **Impact**: Setup confusion

**AC 3.6.2**: Entry point scripts must exist and be functional
- **Current State**: 
  - `run_angela.py` - EXISTS ✅
  - `install_angela.py` - EXISTS ✅
  - `setup.py` - Need to verify
- **Expected**: All entry points documented in README must exist
- **Priority**: HIGH
- **Impact**: Cannot start application

### 3.7 Desktop App WebSocket Implementation Issues

**AC 3.7.1**: Desktop app must have functional WebSocket client to communicate with backend
- **Current State**: WebSocket handlers in `apps/desktop-app/electron_app/main.js` are placeholder stubs that fake success
- **Code Issue**: 
  ```javascript
  ipcMain.on('websocket-connect', (event, { url }) => {
    // Connect to backend WebSocket
    // Will use ws or WebSocket library
    event.reply('websocket-connected', { success: true });
  });
  ```
- **Expected**: Real WebSocket client implementation using `ws` library
- **Priority**: CRITICAL
- **Impact**: Desktop app cannot communicate with backend, all tool calls fail, app is non-functional

**AC 3.7.2**: Desktop app package.json must include ws dependency
- **Current State**: Need to verify if `ws` package is listed in dependencies
- **Expected**: `ws` package must be in dependencies
- **Priority**: CRITICAL
- **Impact**: Cannot establish backend connection

**AC 3.6.3**: Desktop App WebSocket client must be functional
- **Current State**: WebSocket implementation EXISTS in `apps/desktop-app/electron_app/main.js` (lines 877+)
- **Implementation Status**: FULLY IMPLEMENTED ✅
  - Connection management with auto-reconnect
  - Message handling (send/receive)
  - Error handling and reconnection logic
  - IPC handlers for renderer process
- **Backend Status**: WebSocket server FULLY IMPLEMENTED ✅
  - Endpoint at `/ws`
  - ConnectionManager for multiple clients
  - Message handling (ping/pong, module_control)
  - Broadcasting support
- **Actual Issue**: Runtime connection/communication issue, not missing implementation
- **Expected**: Test actual connection and tool execution
- **Priority**: HIGH (changed from CRITICAL)
- **Impact**: Need to verify connection works, not implement from scratch

**AC 3.6.3**: Desktop App WebSocket client must be implemented
- **Current State**: `apps/desktop-app/electron_app/main.js` has placeholder WebSocket code that only returns fake success
- **Code Issue**: 
  ```javascript
  ipcMain.on('websocket-connect', (event, { url }) => {
    // Connect to backend WebSocket
    // Will use ws or WebSocket library
    event.reply('websocket-connected', { success: true });
  });
  ```
- **Expected**: Real WebSocket client implementation using `ws` library
- **Priority**: CRITICAL
- **Impact**: Desktop app cannot communicate with backend, all tool calls fail, app is non-functional

### 3.8 Metrics and Performance Documentation

**AC 3.8.1**: metrics.md must contain accurate and up-to-date information
- **Current State**: metrics.md exists with placeholder values ("--" for most metrics)
- **Expected**: Either populate with real data or mark as "Coming Soon"
- **Priority**: LOW
- **Impact**: Misleading performance claims

## 4. Technical Requirements

### 4.1 Documentation Standards
- All markdown files must use consistent formatting
- All links must be valid (internal and external)
- All code blocks must have proper syntax highlighting
- All file paths must use forward slashes for cross-platform compatibility

### 4.2 File Organization
- LICENSE file must be in project root
- Documentation files should be in docs/ directory with clear index
- Configuration examples should be in config/ or docs/examples/

### 4.3 Version Management
- Single source of truth for version number (e.g., VERSION file or package.json)
- All documentation should reference this single source
- Clear changelog documenting version history

## 5. Out of Scope

- Actual implementation of missing features
- Performance optimization
- Code refactoring
- Adding new features
- Translation updates

## 6. Dependencies

- Access to actual GitHub repository (if different from documented URL)
- Clarification from project maintainers on:
  - Correct version number
  - Availability of prebuilt installers
  - Intended licensing terms

## 7. Assumptions

- The project is intended to be open-source under MIT License
- The GitHub repository URL `https://github.com/catcatAI/Unified-AI-Project` is correct or will be corrected
- The project is actively maintained
- Version 6.2.0 is the intended current version

## 8. Risks

- **Risk 1**: Repository URL may be incorrect, preventing users from accessing the project
  - **Mitigation**: Verify with maintainers or update to correct URL
  
- **Risk 2**: Missing LICENSE file may cause legal issues
  - **Mitigation**: Add proper MIT License file immediately
  
- **Risk 3**: Broken installation instructions may frustrate users
  - **Mitigation**: Test all installation paths and update documentation

## 9. Success Metrics

- All critical issues (CRITICAL priority) resolved: 3 issues (git clone, LICENSE, WebSocket)
- All high priority issues resolved: 2 issues
- Documentation accuracy improved to 100%
- Zero broken links in documentation
- Successful installation following README instructions on all platforms
- Desktop app successfully connects to backend via WebSocket
- All inter-app communication functional

## 10. Timeline Estimate

- **Critical Issues**: 1-2 hours
- **High Priority Issues**: 2-4 hours
- **Medium Priority Issues**: 4-6 hours
- **Low Priority Issues**: 2-3 hours
- **Total Estimated Time**: 9-15 hours
