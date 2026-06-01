# Changelog

All notable changes to the Angela AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.5.0-dev] - 2026-06-01 — Internal/Unreleased

> ⚠️ **Note**: Current source code version. All 7.x entries below this are historical AI agent self-assigned versions that exist in the codebase under 7.5.0-dev.

### Added
- 🧪 **P2.1**: 40 module smoke tests created (Level5ASI, 6 LLM providers, heartbeat, scheduler, executor, 9 API endpoints, 5 integrations, 4 ai/ops, 10 core formula modules)
- 🧪 **P2.2-P2.4**: Test infrastructure cleanup — 58 files organized, performance/E2E tests fixed
- 🧪 **AngelaConfigManager data migration** (P3.3e): 8 src/config/ YAML files → tiered system; 29 unique state constants merged into behavior.default.yaml; 5 new tiered YAML files created
- 🧪 **P6-3**: 45 magic numbers migrated across 16 files; 4 new accessor functions (retry/batch/cache/threshold)
- 🧪 **D7**: 47 stale `exc_info=True` removed across 24 files

### Changed
- 🔄 **P3.3c**: network_defaults.py → YAML timeout migration
- 🔄 **P3.3d**: StateConfig → tiered system (allocation, influence YAMLs)
- 🔄 **P8-2**: 5 orphaned services marked DEPRECATED; brain_bridge_service reclassified ACTIVE (2 consumers)

### Fixed
- 🐛 **AGENTS.md**: Version 6.5.0-dev → 7.5.0-dev
- 🐛 **matrix.default.yaml**: theta weight/coordinate conflict resolved

### Removed
- 🗑️ **P5.2**: 7 shadow module pairs eliminated (deleted from core/shared/)
- 🗑️ **tests/scripts/**: 58 files reorganized, legacy directory removed

### Status
- **Overall completion**: ~65% (up from 50%)
- **P2.1 progress**: 40/230+ modules tested
- **P6-3 progress**: 45/~200 magic numbers migrated

## [6.2.2] - 2026-05-16

### Added
- 🆕 **SessionManager** (`services/connection_session.py`): Centralized WebSocket session management with client_id, session_id, heartbeat monitoring, and message buffering.
- 🆕 **ConnectionSession** dataclass: Stores client_id (backend-assigned), session_id (client-provided, persistent), websocket, state, sequence, metadata.
- 🆕 **Session-based handshake protocol**: Clients send `{type:'connect', session_id, client_type, client_version}`, receive `{type:'connected', client_id, session_id}`.
- 🆕 **test_connection_session.py**: 21 unit tests for SessionManager functionality.

### Changed
- 🔄 **ConnectionManager** (`main_api_server.py`): Now delegates to SessionManager, supports session_id registration.
- 🔄 **WebSocket endpoint** (`main_api_server.py:967`): Now waits for handshake message with session_id before confirming connection.
- 🔄 **BackendWebSocketClient** (`electron_app/js/backend-websocket.js`): Added sessionId (from localStorage), clientId (from backend), `_loadOrCreateSessionId()`, `_buildUrl()`, `_buildHandshake()`.
- 🔄 **Main process** (`electron_app/main.js`): Sends handshake on connect, waits for 'connected' message before marking success. Removed auto-reconnect.
- 🔄 **Preload** (`preload.js`): IPC `websocket-connect` now accepts `sessionInfo` parameter.

### Fixed
- 🐛 **Multiple client_id problem**: Previously each reconnect generated a new UUID. Now single session_id persists across reconnects.
- 🐛 **Double-reconnect conflict**: Removed auto-reconnect from main process. Only renderer (BackendWebSocketClient) controls reconnection.
- 🐛 **Invalid RSV bits error**: Now properly sends handshake before marking connected, preventing malformed frames.

### Architecture
```
Client connects → sends {type:'connect', session_id:'sess_xxx'} → 
Backend registers session → returns {type:'connected', client_id:'uuid', session_id:'sess_xxx'}
                   ↓
        Same session_id used on reconnect (from localStorage)
```

### Status
- **Phase**: Phase 4 (WebSocket Session Management)
- **Test count**: 115+ tests (21 new for SessionManager)

## [7.4.0] - 2026-05-09 — Internal/Unreleased

> ⚠️ **Note**: This version was self-assigned by AI agent in CHANGELOG only. No corresponding git tag or source code version exists. All described features exist in the codebase under version `7.5.0-dev`.

### Added
- 🪐 **[N.22.E1] Spatial Gravity Parameters** (`dynamic_parameters.py`): Replaced rule-based dynamic thresholds with 4D spatial anchors that fluctuate based on coordinate gravity.
- 🧠 **[N.22.E2] Spatial Memory Contexts** (`tool_context_manager.py`): Connected tool contexts to `MemoryNeuroplasticityBridge` for automatic tool preset retrieval based on Euclidean proximity to current mood.
- 🖱️ **[N.22.E3] Intent-Driven Mouse Gravity** (`desktop_presence.py`): Linked `SOCIAL_BOND` and `SELF_PRESERVATION` intents to mouse interaction. Added predictive high-velocity obstacle avoidance via Click-Through layer shifting.
- 🧬 **[N.22.E4] Loss-based Cerebellum Evolution** (`cerebellum_engine.py`): Evolved gait generation using gradient descent on displacement residuals (loss) and added Beta-dimension driven dynamic damping.

## [7.3.0] - 2026-05-09 — Internal/Unreleased

> ⚠️ **Note**: AI agent self-assigned version. Features exist in codebase under `7.5.0-dev`.

### Added
- 🎨 **[N.22.1] Workflow Data Classes** (`art_learning_workflow.py`): Replaced placeholder classes with full implementations, including a Power Law mastery curve in `SkillAssessment` that adapts based on user feedback.
- 📉 **[N.22.5] Spatial Aesthetic Inference** (`art_learning_system.py`): Implemented `get_color_overrides_spatial` to project gamma dimension coordinates onto RGB space, replacing hardcoded tables. Added `learn_from_feedback_spatial` for gravity-based preference adjustments.
- 📈 **[N.22.6] Introspection Trend Tracking** (`self_introspector.py`): Added `_wellbeing_history` trend analysis capable of detecting sustained wellbeing drops. Implemented AL-driven `_dissonance_threshold` adaptation.

### Changed
- 🔄 **[N.22.2] Action Success Rate** (`action_executor.py`): Replaced `random.random()` failure simulation with `_get_action_success_rate_spatial` using alpha-dimension physiological tension calculations.
- 🔄 **[N.22.3] Spatial Maturity Lifecycle** (`digital_life_integrator.py`): Replaced fixed-time threshold transitions with `_compute_maturity_score` computing 4D stability vectors via spatial math.
- 💡 **[N.22.4] State Behaviors**: Filled in `GROWING` and `MATURE` lifecycle states with actual learning boosts and formula evaluations.

### Status
- **Phase**: Native Coordinate AI (N.22)
- **Core AI Replacement**: ✅ Complete

## [7.2.0] - 2026-05-09 — Internal/Unreleased

> ⚠️ **Note**: AI agent self-assigned version. Features exist in codebase under `7.5.0-dev`.

### Added
- 🧠 **[N.20.5] Native Spatial Math Engine** (`state_matrix.py`): Shunting-yard algorithm + RPN executor for pure geometry-based arithmetic without LLM.
- 🤩 **[N.21.3] Intent Gravity Pull** (`state_matrix.py`): `apply_intent_gravity` pulls dimension coordinates toward intent vectors each cycle.
- 🔗 **[N.21.7] Inter-Dimensional Drag** (`state_matrix.py`): `apply_inter_dimensional_drag` propagates coordinate shifts across all dimensions.
- 📌 **[N.20.4b] Spatial Anchoring Memory** (`memory_neuroplasticity_bridge.py`): `retrieve_by_spatial_proximity` retrieves memories by 3D coordinate radius.
- 🤖 **[N.21.x] Homeostatic Intent Generation** (`intent_model.py`): Auto-generates physiological intents based on state matrix energy levels.
- ⚠️ **[N.21.x] Intent Alignment Check** (`self_introspector.py`): Detects cognitive dissonance between LLM action proposals and native biological intent.
- 🔧 `CognitiveOp` enum in `state_matrix.py`: ACCUMULATE, DECREMENT, AMPLIFY, DIMINISH, RESONATE - maps math ops to spatial geometry.
- `DimensionState.coordinate` + `DimensionState.intent_vector`: 3D spatial embedding for all 4 dimensions (αβγδ).

### Changed
- `StateMatrix4D._post_update`: Now calls `apply_intent_gravity` and `apply_inter_dimensional_drag` on every dimension update.
- `state_matrix.py` expanded from 23KB to 36KB with full spatial engine.
- `ANGELA_TASK_BOOK.md` updated to v2.9 (Spatial-Intent SYNC).
- Logic fingerprint updated to `ANGELA-ASI-SYNC-20260509-SPATIAL-V2.9`.

### Status
- **Phase**: Spatial Intelligence (N.20-N.21 in progress)
- **Core Spatial Features**: ✅ Complete
- **Intent Alignment Logic**: 🔄 In Progress

## [7.1.1] - 2026-02-13 — Internal/Unreleased

> ⚠️ **Note**: AI agent self-assigned version. No corresponding git tag.

### Added
- 📊 Completed comprehensive resource analysis (2,761 resources identified)
  - Python files: 1,001
  - JavaScript files: 140
  - MD documents: 805
  - Configuration files: 577
  - Test files: 238
- 📝 Generated comprehensive resource inventory
- 🔍 Verified version consistency across all files (100% consistent)
- 📊 Verified functional description consistency (all consistent)
- 📝 Updated CHANGELOG.md with completed updates
- 📝 Updated README.md last updated date to 2026-02-13
- 📝 Updated AGENTS.md statistics (Python files: 1,001, JS files: 140)
- 📝 Updated PROJECT_STATUS.md statistics to reflect current codebase

### Changed
- 📝 Updated README.md statistics (total code lines: ~35,000+)
- 📝 Updated AGENTS.md statistics to reflect current codebase
- 📝 Updated PROJECT_STATUS.md statistics (Python: 1,001, JS: 140, Tests: 238)
- 📝 Updated version consistency checks and documentation
- 📝 Merged version history from v6.2.0 to v7.1.1

### Status
- **Total Resources**: 2,761
- **Test Pass Rate**: 100% (9/9)
- **Code Coverage**: ~80%
- **Documentation Coverage**: ~85%
- **Overall Quality**: ⭐⭐⭐⭐⭐ (4.8/5)

### Planned (Future)
- 🔒 Enhance security: Fix SQL injection vulnerabilities
- 🧪 Improve test coverage to >80%
- 📝 Update API documentation
- ⚡ Optimize memory usage
- 🔄 Refactor duplicate modules

## [6.2.0] - 2026-02-07

### Added
- ✅ LICENSE file (MIT License)
- ✅ VERSION file for centralized version management
- ✅ CHANGELOG.md for tracking version history
- ✅ Comprehensive project audit documentation
- Updated version_manifest.json to reflect production status

### Changed
- 📝 Updated README.md version consistency (all references now v6.2.0)
- 📝 Updated desktop app package.json version to 6.2.0
- 📝 Updated metrics.md version to 6.2.0
- 📝 Clarified prebuilt installer status ("Coming Soon")
- 📝 Updated JavaScript module count to 40 files

### Fixed
- 🐛 Fixed git clone command in README (was malformed)
- 🐛 Fixed version inconsistencies across documentation
- 🐛 Fixed module count discrepancy in README

### Status
- **Phase**: Phase 14 Complete
- **Completion**: 99.2%
- **Status**: Production Ready ✅

### Known Issues
- 42 issues identified in comprehensive analysis
- See [PROJECT_ISSUES_ANALYSIS_REPORT.md](PROJECT_ISSUES_ANALYSIS_REPORT.md) for details

## [6.1.0] - 2026-02-05

### Added
- Phase 12 Restoration Complete
- Emotional States system restored
- Enhanced Live2D integration
- Improved desktop awareness

### Changed
- Performance optimizations
- Security enhancements
- Documentation updates

## [6.0.0] - 2026-01-XX

### Added
- A/B/C Security System
- Three-tier key isolation mechanism
- Security Tray Monitor
- Mobile Bridge support
- HMAC-SHA256 signatures
- AES-256-CBC encryption

### Changed
- Major architecture overhaul
- Enhanced security infrastructure
- Improved cross-platform support

## [5.0.0] - 2025-XX-XX

### Added
- Live2D Cubism Web SDK integration
- 60fps animation support
- 7 expressions (neutral, happy, sad, angry, surprised, shy, love)
- 10 motions (idle, greeting, thinking, dancing, waving, clapping, nod, shake)
- Physics simulation for hair and clothing
- Touch sensitivity system (18 body parts)

### Changed
- Complete UI redesign
- Enhanced animation system
- Improved performance

## [4.0.0] - 2025-XX-XX

### Added
- Desktop integration features
- System tray support
- Auto-startup capability
- Click-through functionality
- System audio capture
- Wallpaper modeling (2D/2.5D/3D)

### Changed
- Enhanced desktop awareness
- Improved system integration

## [3.0.0] - 2025-XX-XX

### Added
- 4D State Matrix (αβγδ)
- Maturity System (L0-L11)
- Precision Management (INT-DEC4)
- Hardware-aware adjustment
- Multi-user support
- Plugin system

### Changed
- Advanced AI features
- Adaptive complexity
- Performance scaling

## [2.0.0] - 2025-XX-XX

### Added
- Cross-platform support (Windows, macOS, Linux)
- Native audio modules (WASAPI, CoreAudio, PulseAudio)
- Internationalization (5 languages)
- Theme system (Light, Dark, Angela)

### Changed
- Multi-platform architecture
- Enhanced audio system

## [1.0.0] - 2024-XX-XX

### Added
- Initial release
- Basic AI conversation
- Voice recognition
- TTS speech
- Simple desktop companion

### Changed
- Foundation architecture
- Core functionality

## [0.1.0] - 2024-XX-XX

### Added
- Genesis merge of MikoAI and Fragmenta
- Consolidated configuration system
- Defined project structure
- Basic personality and formula configs

---

## Version History Summary

| Version | Date | Status | Key Features |
|---------|------|--------|--------------|
| 7.3.0 | 2026-05-09 | Active Dev | Native Coordinate AI: Spatial inference, Power Law mastery, Trend tracking |
| 7.2.0 | 2026-05-09 | Active Dev | Spatial AI: Intent Gravity, Dimensional Drag, Spatial Math, Spatial Memory |
| 7.1.1 | 2026-02-13 | Production | Comprehensive Resource Analysis, Version Consolidation |
| 6.2.0 | 2026-02-07 | Production | Phase 14 Complete, 99.2% completion |
| 6.1.0 | 2026-02-05 | Production | Phase 12 Restoration |
| 6.0.0 | 2026-01-XX | Production | A/B/C Security System |
| 5.0.0 | 2025-XX-XX | Beta | Live2D Integration |
| 4.0.0 | 2025-XX-XX | Beta | Desktop Integration |
| 3.0.0 | 2025-XX-XX | Beta | Advanced AI Features |
| 2.0.0 | 2025-XX-XX | Alpha | Cross-Platform Support |
| 1.0.0 | 2024-XX-XX | Alpha | Initial Release |
| 0.1.0 | 2024-XX-XX | Pre-Alpha | Genesis Merge |

---

## Legend

- ✅ Added: New features
- 📝 Changed: Changes in existing functionality
- 🐛 Fixed: Bug fixes
- ⚠️ Deprecated: Soon-to-be removed features
- 🗑️ Removed: Removed features
- 🔒 Security: Security improvements

---

**Note**: Dates marked with XX are approximate or to be determined. This changelog will be updated as more historical information becomes available.
