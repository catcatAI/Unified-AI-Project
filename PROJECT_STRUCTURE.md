# Angela AI Project Structure

This document provides a comprehensive overview of the Angela AI project structure, directory organization, and file placement principles.

## 📁 Directory Structure Overview

```
angela-ai/
├── apps/
│   └── backend/                 # Backend application
│       ├── src/                 # Source code
│       │   ├── ai/              # AI systems
│       │   ├── api/             # API endpoints
│       │   ├── core/            # Core components
│       │   │   └── autonomous/  # Autonomous life systems
│       │   ├── game/            # Desktop Pet game
│       │   └── services/        # Service layer
│       ├── debug/               # Debug utilities
│       ├── tests/               # Backend tests
│       └── tools/               # Backend tools
├── archive/                     # Archived/deprecated code
├── cli/                         # Command-line interface
├── config/                      # Configuration files
├── data/                        # Data storage
│   ├── cache/                   # Cache files
│   ├── memories/                # Memory storage
│   └── models/                  # ML models
├── docs/                        # Documentation
│   └── screenshots/             # Screenshots
├── logs/                        # Log files
├── resources/                   # Static resources
│   ├── audio/                   # Audio files
│   ├── images/                  # Image assets
│   └── models/                  # Live2D models
├── scripts/                     # Utility scripts
│   ├── audit/                   # Audit/check scripts
│   ├── fixes/                   # Fix/repair scripts
│   └── debug/                   # Debug/diagnostic scripts
├── temp/                        # Temporary files
└── tests/                       # Test suites
    └── game/                    # Game tests
```

## 📂 Directory Purposes

### `/apps/backend/`
Main backend application containing all server-side code.

- **`src/ai/`** - AI systems including:
  - Memory systems (CDM, LU, HSM, HAM)
  - Learning systems
  - Natural language processing
  - Personality modeling

- **`src/api/`** - FastAPI endpoints and API routes

- **`src/core/`** - Core business logic
  - **`autonomous/`** - Autonomous life systems (26 modules)
    - Biological systems (endocrine, nervous, tactile)
    - Digital identity and self-awareness
    - Memory and neuroplasticity
    - Desktop interaction and presence
    - Action execution and behavior

- **`src/game/`** - Desktop Pet implementation
  - `desktop_pet.py` - Main Desktop Pet class
  - `desktop_pet_actor.py` - Ray actor wrapper
  - `economy_manager.py` - In-game economy
  - `angela.py` - Angela character definition

### `/archive/`
Deprecated and archived code that is no longer in use but kept for reference.

- Old versions of systems
- Backup before major changes
- Deprecated scripts and tools

### `/cli/`
Command-line interface implementation.

- `main.py` - CLI entry point
- `commands/` - Individual CLI commands
- `utils/` - CLI utilities

### `/config/`
Configuration files for the application.

- `angela_config.yaml` - Main configuration
- Environment-specific configs

### `/data/`
Runtime data storage.

- **`cache/`** - Temporary cache files
- **`memories/`** - Persistent memory storage
- **`models/`** - Trained ML models

### `/docs/`
Documentation files.

- **`screenshots/`** - Screenshot assets
- User guides
- Architecture diagrams

### `/logs/`
Application log files.

### `/resources/`
Static resource files.

- **`audio/`** - Sound effects, music, voice files
- **`images/`** - Icons, backgrounds, UI assets
- **`models/`** - Live2D model files

### `/scripts/`
Utility scripts organized by purpose:

- **`audit/`** - System audit and quality check scripts
  - `check_*.py` - Various system checks
  - `comprehensive_*.py` - Comprehensive audits

- **`fixes/`** - Fix and repair scripts
  - `fix_*.py` - Specific fix implementations
  - Auto-fix utilities

- **`debug/`** - Debug and diagnostic scripts
  - `debug_*.py` - Debugging utilities
  - Diagnostic tools

### `/tests/`
Test suites.

- **`game/`** - Desktop Pet tests
- Integration tests
- Unit tests

## 📋 File Organization Principles

### 1. **Root Directory Cleanliness**
Root directory should only contain:
- Entry point scripts (`run_angela.py`, `setup.py`)
- Configuration files (`requirements.txt`, `.gitignore`)
- Documentation (`README.md`, `LICENSE`)
- No utility scripts - all scripts go to `/scripts/`

### 2. **Scripts Organization**
All scripts must be categorized and placed in appropriate subdirectories:

| Pattern | Destination | Purpose |
|---------|-------------|---------|
| `check_*.py` | `scripts/audit/` | System checks |
| `comprehensive_*.py` | `scripts/audit/` | Comprehensive audits |
| `fix_*.py` | `scripts/fixes/` | Bug fixes |
| `debug_*.py` | `scripts/debug/` | Debugging |
| `*_backup.py` | `archive/` | Backups |
| `*_temp.py` | `archive/` | Temp files |

### 3. **Backend Code Organization**

- **Core systems** go to `apps/backend/src/core/`
- **AI modules** go to `apps/backend/src/ai/`
- **Game code** goes to `apps/backend/src/game/`
- **Tests** go to `apps/backend/tests/` or `/tests/`

### 4. **Import Paths**

Use relative imports within packages:
```python
# Within apps/backend/src/core/autonomous/
from .live2d_integration import Live2DIntegration
from ..action_executor import ActionExecutor

# From other packages
from apps.backend.src.core.autonomous import DesktopPet
```

### 5. **Naming Conventions**

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_CASE`

## 🔄 Maintenance Guidelines

### Regular Cleanup Tasks

1. **Monthly**
   - Review and archive old scripts
   - Clean up temporary files
   - Rotate log files

2. **Quarterly**
   - Review archive/ directory size
   - Clean up old cache files
   - Update documentation

3. **Before Releases**
   - Run all audit scripts
   - Verify no scripts in root
   - Check import paths
   - Update PROJECT_STRUCTURE.md

### Adding New Files

1. Choose appropriate directory based on purpose
2. Follow naming conventions
3. Update this document if adding new directories
4. Ensure proper imports
5. Add tests if applicable

### Moving/Removing Files

1. Check for import dependencies
2. Update all references
3. Test after moving
4. Update this document
5. Document reason in commit message

## 📊 Current Statistics

- **Total Python Files**: ~477 (apps/backend/src/)
- **JavaScript Modules**: 52 (electron_app/js/)
- **Core System Files**: 26 (autonomous/)
- **AI Agent Files**: 20 (agents/)
- **Scripts**: 50+ (organized in subdirectories)
- **Tests**: 100+ (tests/)
- **Lines of Code**: ~30,000+

## 🔍 Quick Reference

| Want to... | Look in... |
|------------|-----------|
| Run Angela | `run_angela.py` |
| Configure | `config/angela_config.yaml` |
| Fix bugs | `scripts/fixes/` |
| Debug | `scripts/debug/` |
| Check system | `scripts/audit/` |
| View logs | `logs/` |
| Add Desktop Pet features | `apps/backend/src/game/` |
| Modify AI systems | `apps/backend/src/ai/` |
| Update core systems | `apps/backend/src/core/autonomous/` |

---

Last Updated: 2026-02-02
Version: 6.0.0
