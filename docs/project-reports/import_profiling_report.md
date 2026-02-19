# Backend Import Performance Analysis Report

**Date**: 2026-02-16  
**Total Import Time**: **36.20 seconds**  
**Target**: < 2 seconds  
**Status**: ❌ **CRITICAL - 18x slower than target**

---

## Executive Summary

The backend import time of **36.20 seconds** is unacceptable and severely impacts:
- ✗ Test collection speed (pytest --collect-only)
- ✗ Development iteration speed (auto-reload)
- ✗ Server startup time
- ✗ CI/CD pipeline performance

**Root Cause**: Heavy machine learning libraries (sklearn, scipy, chromadb) are being loaded **synchronously at module import time** instead of being lazily loaded when needed.

---

## Top 5 Blocking Operations

| Rank | Module | Time | Impact |
|------|--------|------|--------|
| 1 | `sklearn.linear_model` | **15.30s** | Loaded via `ai.ops.capacity_planner` |
| 2 | `scipy.stats` | **7.61s** | ML dependency |
| 3 | `fastapi` | **5.52s** | ✓ Acceptable - core framework |
| 4 | `chromadb` | **5.05s** | Loaded via `ai.memory.vector_store` |
| 5 | `sklearn.utils` | **14.23s** | Part of sklearn loading |

**Total ML library overhead**: ~27 seconds (75% of total import time)

---

## Import Chain Analysis

### Critical Path 1: sklearn Loading (15.3s)
```
main_api_server.py (36.2s)
  └─> api.router (16.2s)
       └─> api.routes.ops_routes (15.8s)
            └─> ai.ops.intelligent_ops_manager (15.75s)
                 └─> ai.ops.capacity_planner (15.72s)
                      └─> sklearn.linear_model (15.30s)  ⚠️ BLOCKING IMPORT
```

**File**: `apps/backend/src/ai/ops/capacity_planner.py:24-28`
```python
# ❌ BLOCKING: Loads at module scope
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not found...")
```

### Critical Path 2: chromadb Loading (5.0s)
```
main_api_server.py (36.2s)
  └─> services.angela_llm_service (5.31s)
       └─> ai.memory.ham_memory.ham_manager (5.25s)
            └─> ai.memory.vector_store (5.06s)
                 └─> chromadb (5.05s)  ⚠️ BLOCKING IMPORT
```

**File**: `apps/backend/src/ai/memory/vector_store.py:8`
```python
# ❌ BLOCKING: Loads at module scope
import chromadb
from chromadb.utils import embedding_functions
```

---

## Detailed Findings

### 1. Machine Learning Libraries (15.3s - **42% of total time**)

**Problem**: `sklearn` is imported at module load time but only used for capacity prediction, which is not a critical hot path.

**Location**: `apps/backend/src/ai/ops/capacity_planner.py`

**Current Code**:
```python
# Lines 21-28
SKLEARN_AVAILABLE = False
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not found. CapacityPlanner will use simpler prediction models.")
```

**Impact**:
- Loads entire sklearn package (15.3s)
- Blocks ALL backend imports
- Not needed for core API functionality

### 2. Vector Database (5.0s - **14% of total time**)

**Problem**: `chromadb` is imported at module load time but only needed for memory operations.

**Location**: `apps/backend/src/ai/memory/vector_store.py`

**Current Code**:
```python
# Lines 6-9
import logging
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.utils import embedding_functions
```

**Impact**:
- Loads chromadb library (5.0s)
- Blocks memory service initialization
- Not needed until actual memory operations

### 3. Additional Slow Imports

**Other files loading sklearn** (found via grep):
- `core/knowledge/unified_knowledge_graph.py`
- `core/io/io_intelligence_orchestrator.py`
- `core/tools/logic_model/evaluate_logic_model.py`
- `core/fusion/multimodal_fusion_engine.py`
- `core/evolution/emergence_engine.py`
- `core/evolution/autonomous_evolution_engine.py`
- `core/ethics/ethics_manager.py`
- `core/creativity/creative_breakthrough_engine.py`
- `core/cognitive/cognitive_constraint_engine.py`
- `core/metacognition/metacognitive_capabilities_engine.py`

**Note**: These may not all be in the import path, but represent potential future issues.

---

## Recommended Solutions

### Solution 1: Lazy Loading for sklearn (PRIORITY 1)

**File**: `apps/backend/src/ai/ops/capacity_planner.py`

**Before**:
```python
SKLEARN_AVAILABLE = False
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn not found...")
```

**After**:
```python
# Module-level globals for lazy loading
_sklearn_models = None
SKLEARN_AVAILABLE = None  # None = not checked yet

def _ensure_sklearn():
    """Lazy-load sklearn only when needed."""
    global _sklearn_models, SKLEARN_AVAILABLE
    
    if SKLEARN_AVAILABLE is not None:
        return SKLEARN_AVAILABLE
    
    try:
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_squared_error
        _sklearn_models = {
            'LinearRegression': LinearRegression,
            'mean_squared_error': mean_squared_error
        }
        SKLEARN_AVAILABLE = True
        logger.info("sklearn loaded successfully (lazy)")
    except ImportError:
        logger.warning("sklearn not available, using fallback models")
        SKLEARN_AVAILABLE = False
    
    return SKLEARN_AVAILABLE

def _predict_with_sklearn(...):
    """Use sklearn models - lazy-loaded."""
    if not _ensure_sklearn():
        return _predict_simple_fallback(...)
    
    LinearRegression = _sklearn_models['LinearRegression']
    # ... use sklearn models
```

**Expected Impact**: -15.3s (import time: 36.2s → 20.9s)

### Solution 2: Lazy Loading for chromadb (PRIORITY 2)

**File**: `apps/backend/src/ai/memory/vector_store.py`

**Before**:
```python
import chromadb
from chromadb.utils import embedding_functions

class VectorMemoryStore:
    def __init__(self, persist_directory: Optional[str] = None):
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
```

**After**:
```python
# Lazy import - only load when needed
_chromadb = None

def _ensure_chromadb():
    """Lazy-load chromadb only when VectorMemoryStore is instantiated."""
    global _chromadb
    if _chromadb is None:
        import chromadb
        _chromadb = chromadb
    return _chromadb

class VectorMemoryStore:
    def __init__(self, persist_directory: Optional[str] = None):
        chromadb = _ensure_chromadb()
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
```

**Expected Impact**: -5.0s (import time: 20.9s → 15.9s)

### Solution 3: Deferred Router Registration (PRIORITY 3)

**File**: `apps/backend/src/services/main_api_server.py`

**Current**: Line 295 imports `api.router` at module scope, triggering all route imports.

**Recommendation**: Defer router registration until app startup event.

**Before**:
```python
from api.router import router as api_v1_router

# Later...
app.include_router(api_v1_router)
```

**After**:
```python
@app.on_event("startup")
async def startup_event():
    """Load heavy routes only on actual startup."""
    from api.router import router as api_v1_router
    app.include_router(api_v1_router)
    logger.info("API routes loaded")
```

**Expected Impact**: -10-15s (import time: 15.9s → ~5s)

**Trade-off**: Routes won't be available during import (acceptable - they're only needed after server starts).

---

## Implementation Priority

### Phase 1: Quick Wins (P1-2)
1. ✅ **Profile imports** (completed)
2. 🔧 **Implement lazy loading for sklearn** - Expected: -15s
3. 🔧 **Implement lazy loading for chromadb** - Expected: -5s
4. ✅ **Verify import time < 20s** (target: 20s → 16s)

### Phase 2: Optimization (P2)
5. 🔧 **Defer router registration** - Expected: -10s
6. ✅ **Verify import time < 10s** (target: 16s → 6s)

### Phase 3: Polish (P3)
7. 🔧 **Apply lazy loading to other sklearn imports** (10 files)
8. 🔧 **Add import time monitoring to CI/CD**
9. ✅ **Verify import time < 2s target**

---

## Verification Commands

### Before Refactoring
```bash
cd apps/backend
python -c "import time; s=time.time(); from src.services.main_api_server import app; print(f'{time.time()-s:.2f}s')"
# Current: 36.20s
```

### After Phase 1 (Target: <20s)
```bash
cd apps/backend
python -c "import time; s=time.time(); from src.services.main_api_server import app; print(f'{time.time()-s:.2f}s')"
# Expected: ~16s
```

### After Phase 2 (Target: <10s)
```bash
cd apps/backend
python -c "import time; s=time.time(); from src.services.main_api_server import app; print(f'{time.time()-s:.2f}s')"
# Expected: ~6s
```

### Test Collection Speed
```bash
# Before: Timeout (>120s)
pytest --collect-only --timeout=30

# After Phase 1: Should complete
pytest --collect-only --timeout=60

# After Phase 2: Fast collection
pytest --collect-only --timeout=30
```

---

## Files Requiring Modification

### Phase 1 (P1-2 Implementation)
1. `apps/backend/src/ai/ops/capacity_planner.py` - Lazy sklearn loading
2. `apps/backend/src/ai/memory/vector_store.py` - Lazy chromadb loading

### Phase 2 (Optimization)
3. `apps/backend/src/services/main_api_server.py` - Deferred router registration
4. `apps/backend/src/api/router.py` - Review and optimize route imports

### Phase 3 (Polish)
5. 10 additional files with sklearn imports (see "Additional Slow Imports")

---

## Success Metrics

| Metric | Before | Phase 1 Target | Phase 2 Target | Final Target |
|--------|--------|----------------|----------------|--------------|
| Import Time | 36.2s | <20s | <10s | <2s |
| Test Collection | Timeout | <60s | <30s | <10s |
| Server Startup | ~40s | ~25s | ~15s | <5s |
| Dev Iteration | Blocked | Slow | Acceptable | Fast |

---

## Additional Notes

### Why This Matters
1. **Development Experience**: 36s import time means every code reload takes 36s
2. **Test Performance**: pytest can't collect tests in reasonable time
3. **CI/CD**: Slow tests = slow deployments
4. **Production**: Slow startup = longer downtime during deploys

### Pattern to Follow
```python
# ❌ BAD: Eager import at module scope
import heavy_library

# ✓ GOOD: Lazy import when needed
_heavy_lib = None

def _ensure_heavy_lib():
    global _heavy_lib
    if _heavy_lib is None:
        import heavy_library
        _heavy_lib = heavy_library
    return _heavy_lib

def function_using_lib():
    lib = _ensure_heavy_lib()
    lib.do_something()
```

### Alternative: Import Hooks (Advanced)
For future consideration: Use Python's import hooks to automatically lazy-load heavy modules.

---

## Profiling Data

Full profiling data available in:
- `apps/backend/import_timing.txt` - Raw importtime output
- `apps/backend/import_analysis.json` - Parsed analysis data
- `apps/backend/analyze_imports.py` - Analysis script

---

**Generated**: 2026-02-16 00:10 UTC+8  
**Tool**: Python 3.12.10 `-X importtime` profiler  
**Analysis Script**: `analyze_imports.py`
