# SUPERSEDED — Archived 2026-08-13

This folder (`docs/03-technical-architecture/ai-components/`) was archived because its
contents describe the **`src/core_ai/` module layout, which no longer exists** (the
code was restructured into `apps/backend/src/ai/` and `apps/backend/src/core/`).

The modules it documented are now readable directly from source. Some still exist under
new paths (e.g. `emotion_system.py` → `ai/alignment/emotion_system.py`,
`tool_dispatcher` → `core/tools/js_tool_dispatcher`); others were deleted entirely
(`personality_manager`, `ham_memory_manager`, `deep_mapper`).

Content is preserved here for historical reference only. Do not link to these files
from current documentation.
