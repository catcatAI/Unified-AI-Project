# Planning Folder Consolidation Proposal

Date: 2025-08-06
Owner: Architecture / PMO
Status: Draft

## Goals
- Reduce duplication and drift across planning documents.
- Clarify canonical sources (what to read first) and archive superseded materials.
- Make weekly planning/status workflows predictable and linkable.

## Inventory by Area (high-level)

- core-development/
  - agi-development-plan.md
  - architecture-deep-dive.md
  - implementation-plan-v2.md
  - technical-implementation-roadmap.md
  - LLM_ROUTING_AND_ADAPTATION_PLAN.md
  - project-status-assessment.md
- project-management/planning-docs/
  - PROJECT_CHARTER.md
  - ROADMAP.md
  - CURRENT_STATUS_AND_ACTION_PLAN.md
  - HORIZONTAL_ALIGNMENT_TASK.md
  - HORIZONTAL_ALIGNMENT_ROADMAP.md
  - component-improvement-plan.md
  - content-organization.md
  - project-status-summary.md
  - todo-placeholders.md
- project-management/status-reports/
  - API_STATUS_REPORT*.md, PROJECT_STATUS_SUMMARY.md, PROJECT_UPDATE_STATUS.md
- project-management/implementation-reports/
  - (historical) workspace-cleanup-summary.md, final-workspace-organization-report.md, …
- documentation/
  - documentation-index.md, reorganization-plan.md, CODE_DOCUMENTATION_CONSISTENCY_CHECK.md
- philosophy/
  - PHILOSOPHY_AND_VISION.md, agi-concepts.md, AGI_ARCHITECTURE_AND_TRAINING.md
- external-analysis/
  - competitive-analysis.md, agi-assessment.md, FRONTEND_BACKEND_COMPARISON.md
- NEW: project-management/planning-docs/AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md

## Overlap and Issues (what to merge or de-duplicate)

1) Technical plans overlap
- Files: core-development/implementation-plan-v2.md, technical-implementation-roadmap.md, architecture-deep-dive.md, agi-development-plan.md
- Issue: These mix strategy, roadmap, and deep-dive. Readers don’t know which is canonical.
- Proposal:
  - Create a single canonical: core-development/TECHNICAL_ROADMAP.md
    - Sections: Architectural Overview, Roadmap (near/mid/long-term), Deep-dive Appendices (linking to detailed docs), LLM routing & adaptation summary
  - Supersede/Archive: implementation-plan-v2.md, technical-implementation-roadmap.md into archive/ with header pointing to TECHNICAL_ROADMAP.md
  - Keep architecture-deep-dive.md but link as appendix from TECHNICAL_ROADMAP.md

2) PM planning vs status vs charter
- Files: PROJECT_CHARTER.md, ROADMAP.md, CURRENT_STATUS_AND_ACTION_PLAN.md, project-status-summary.md
- Issue: Status vs plan split across multiple files with repeated summaries.
- Proposal:
  - Keep PROJECT_CHARTER.md (foundational) and ROADMAP.md (business roadmap) as canonical.
  - Merge CURRENT_STATUS_AND_ACTION_PLAN.md and project-status-summary.md into STATUS_AND_ACTIONS.md (rolling document, weekly updated).
  - Update documentation-index.md to reference the new canonical set.

3) Horizontal alignment docs
- Files: HORIZONTAL_ALIGNMENT_TASK.md, HORIZONTAL_ALIGNMENT_ROADMAP.md
- Issue: Two docs for similar theme.
- Proposal: Merge into HORIZONTAL_ALIGNMENT_PLAN.md with Task (short-term) and Roadmap (mid-term) sections.

4) New AGI & Data Life plan integration
- File: project-management/planning-docs/AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md (new)
- Issue: Needs to be linked from ROADMAP and TECHNICAL_ROADMAP.
- Proposal: Add links in ROADMAP.md and TECHNICAL_ROADMAP.md; add to documentation-index.md under Development Plans.

5) Implementation reports sprawl
- Directory: project-management/implementation-reports/
- Issue: Many historical reports; valuable but noisy.
- Proposal: Keep as archive; add an index README.md summarizing key reports and last-updated timeline.

6) Documentation governance
- Files: documentation-index.md, reorganization-plan.md, CODE_DOCUMENTATION_CONSISTENCY_CHECK.md
- Issue: Multiple meta-docs without a single source of truth.
- Proposal: documentation-index.md is canonical. Add a Governance section pointing to consistency checks and reorg plan. Deprecate reorganization-plan.md once this consolidation completes (move content into Governance).

## Concrete Actions (batchable)

- Create core-development/TECHNICAL_ROADMAP.md (new canonical)
  - Lift the most current content from technical-implementation-roadmap.md and implementation-plan-v2.md
  - Add pointers to architecture-deep-dive.md and LLM_ROUTING_AND_ADAPTATION_PLAN.md
- Create project-management/planning-docs/STATUS_AND_ACTIONS.md
  - Merge CURRENT_STATUS_AND_ACTION_PLAN.md + project-status-summary.md
- Merge HORIZONTAL_ALIGNMENT_TASK.md + HORIZONTAL_ALIGNMENT_ROADMAP.md → HORIZONTAL_ALIGNMENT_PLAN.md
- Add planning/project-management/implementation-reports/README.md (index, short abstracts)
- Update documentation-index.md to:
  - Point to: PROJECT_CHARTER.md, ROADMAP.md, STATUS_AND_ACTIONS.md, TECHNICAL_ROADMAP.md, AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md
- Add deprecation banners to superseded files (top-of-file note with link to canonical)

## Naming/Placement Guidelines
- Plans under project-management/planning-docs/
- Technical deep-dives under core-development/
- Status under project-management/status-reports/ (or the consolidated STATUS_AND_ACTIONS.md if single rolling doc)
- Historical/one-off implementation reports remain under implementation-reports/

## Open Questions
- Should status remain as weekly separate files (status-reports/) or single rolling doc (STATUS_AND_ACTIONS.md)?
- Do we want a single BUSINESS_ROADMAP vs TECHNICAL_ROADMAP split explicitly documented in the root docs index?
- Who owns documentation governance (approvals, PR templates, review cadence)?

## Rollout Plan
- Phase 1 (1–2 days): Create new canonical docs, add deprecation banners, update documentation-index.md
- Phase 2 (next sprint): Merge HORIZONTAL_* docs, create implementation-reports/README.md, prune dead links
- Phase 3 (ongoing): Quarterly doc hygiene; CI check for stale links and duplicate headings

## Success Criteria
- New joiners can locate charter, business roadmap, technical roadmap, status/action in <3 clicks.
- No more than one active doc per planning theme.
- Documentation index reflects latest reality; broken links < 1%.
