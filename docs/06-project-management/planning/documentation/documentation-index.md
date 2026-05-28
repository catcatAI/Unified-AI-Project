# Planning Documents Index

## 1. Overview

This document serves as the central index for all planning, architectural, and strategic documents related to the Unified-AI-Project. All documents have been organized into the `planning/` directory, categorized by function.

---

## 2. Directory Structure

```
planning/
├── README.md                       # Overview of the planning directory
├── archive/                        # Historical or superseded documents
│   └── RESTRUCTURING_PLAN.md
├── core-development/               # Core AGI development and technical plans
│   ├── agi-development-plan.md
│   ├── architecture-deep-dive.md
│   ├── LLM_ROUTING_AND_ADAPTATION_PLAN.md
│   ├── project-status-assessment.md
│   └── TECHNICAL_ROADMAP.md
├── documentation/                  # Documents related to planning and organization
│   ├── CODE_DOCUMENTATION_CONSISTENCY_CHECK.md
│   ├── documentation-index.md      # This file
│   └── reorganization-plan.md
├── external-analysis/              # Analysis of external factors and projects
│   ├── agi-assessment.md
│   ├── competitive-analysis.md
│   └── FRONTEND_BACKEND_COMPARISON.md
├── philosophy/                     # Core concepts and philosophical underpinnings
│   ├── agi-concepts.md
│   └── PHILOSOPHY_AND_VISION.md
└── project-management/             # Project management, status, and reports
    ├── implementation-reports/     # Reports on specific implementation tasks
    │   ├── BACKEND_TEST_ANALYSIS_REPORT.md
    │   ├── cleanup-summary.md
    │   ├── configuration-update-summary.md
    │   ├── debugging_summary.md
    │   ├── documentation-link-audit-report.md
    │   ├── documentation-link-audit-update.md
    │   ├── FINAL_MD_UPDATE_REPORT.md
    │   ├── final-workspace-organization-report.md
    │   ├── legacy-project-summary.md
    │   ├── merge-restructure-plan.md
    │   ├── project-continuation-summary.md
    │   ├── project-health-audit.md
    │   ├── refactoring_sprint_1_summary.md
    │   ├── rovo-dev-implementation-final-report.md
    │   ├── RUNTIME_ISSUES_REPORT.md
    │   ├── UPDATED_MD_SUMMARY.md
    │   ├── workspace-cleanup-summary.md
    │   └── workspace-integration-summary.md
    ├── planning-docs/              # General planning documents
    │   ├── component-improvement-plan.md
    │   ├── content-organization.md
    │   ├── STATUS_AND_ACTIONS.md
    │   ├── HORIZONTAL_ALIGNMENT_PLAN.md
    │   ├── PROJECT_CHARTER.md
    │   ├── project-status-summary.md
    │   ├── ROADMAP.md
    │   ├── test_plan.md
    │   └── todo-placeholders.md
    └── status-reports/             # High-level project status reports
        ├── API_STATUS_REPORT.md
        ├── PROJECT_AUDIT.md
        ├── PROJECT_UPDATE_STATUS.md
        └── PROJECT_STATUS_SUMMARY.md
```

---

## 3. Document Index by Category

### 3.1 Core Development

*   **[AGI Development Plan](../core-development/agi-development-plan.md)**: Outlines the four-phase roadmap to advance the project from AGI Level 1 to Level 3+.
*   **[Architecture Deep Dive](../core-development/architecture-deep-dive.md)**: Details the unique architectural pillars like HSP, Deep Mapping, UID, and the "Data Life" concept.
*   **[LLM Routing and Adaptation Plan](../core-development/LLM_ROUTING_AND_ADAPTATION_PLAN.md)**: A plan for routing and adapting Large Language Models within the system.
*   **[Project Status Assessment](../core-development/project-status-assessment.md)**: An overall assessment of the project's technical status, strengths, and weaknesses.
*   **[Technical Roadmap (Canonical)](../core-development/TECHNICAL_ROADMAP.md)**: Consolidated, code-level plan linking architecture, roadmap (near/mid/long), and deep-dive appendices.

### 3.2 Project Management

*   **Status Reports (`./project-management/status-reports/`)**: Contains high-level summaries of the project's overall status and progress.
    *   `API_STATUS_REPORT.md`
    *   `PROJECT_AUDIT.md`
    *   `PROJECT_UPDATE_STATUS.md`
    *   `PROJECT_STATUS_SUMMARY.md`
*   **Planning Docs (`./project-management/planning-docs/`)**: Holds various documents related to project planning and organization.
    *   `PROJECT_CHARTER.md`
    *   `ROADMAP.md`
    *   `STATUS_AND_ACTIONS.md` (rolling)
    *   `AGI_AND_DATA_LIFE_IMPLEMENTATION_PLAN.md`
    *   `PERCEPTION_ACTION_FEEDBACK_PLAN.md`
    *   `ROBUSTNESS_AND_SAFETY_HARDENING_PLAN.md`
    *   `HORIZONTAL_ALIGNMENT_PLAN.md`
    *   `APP_DESKTOP_PLANS_INDEX.md`
    *   `CROSS_MODULE_IMPACT_MATRIX.md`
    *   `component-improvement-plan.md`
    *   `content-organization.md`
    *   `test_plan.md`
    *   `todo-placeholders.md`
*   **Implementation Reports (`./project-management/implementation-reports/`)**: Contains detailed reports on the completion of specific development and refactoring tasks.
    *   `README.md` (index)
    *   `Unified-AI-Project/implementation_plan.md` (DEPRECATED — see `core-development/TECHNICAL_ROADMAP.md` and `project-management/planning-docs/STATUS_AND_ACTIONS.md`)
    *   `BACKEND_TEST_ANALYSIS_REPORT.md`
    *   `cleanup-summary.md`
    *   `configuration-update-summary.md`
    *   `debugging_summary.md`
    *   `documentation-link-audit-report.md`
    *   `documentation-link-audit-update.md`
    *   `FINAL_MD_UPDATE_REPORT.md`
    *   `final-workspace-organization-report.md`
    *   `legacy-project-summary.md`
    *   `merge-restructure-plan.md`
    *   `project-continuation-summary.md`
    *   `project-health-audit.md`
    *   `refactoring_sprint_1_summary.md`
    *   `rovo-dev-implementation-final-report.md`
    *   `RUNTIME_ISSUES_REPORT.md`
    *   `UPDATED_MD_SUMMARY.md`
    *   `workspace-cleanup-summary.md`
    *   `workspace-integration-summary.md`

### 3.3 App-specific Plans

- Desktop App Proposals (`Unified-AI-Project/apps/desktop-app/docs/`):
  - RESPONSIVE_LAYOUT_PROPOSAL.md
  - STATE_MANAGEMENT_PROPOSAL.md
  - IPC_REFACTOR_PROPOSAL.md
  - SECURITY_HARDENING_PROPOSAL.md
  - HISTORY_MANAGEMENT_PROPOSAL.md
  - ELECTRON_APP_IMPROVEMENTS.md
  - PERFORMANCE_OPTIMIZATION_PROPOSAL.md
  - USER_FEEDBACK_PROPOSAL.md
- Frontend Dashboard Reports (`Unified-AI-Project/apps/frontend-dashboard/`):
  - CONSOLE_ERRORS_FIXED.md
  - DATA_INTEGRATION_SUMMARY.md

### 3.4 Documentation & Organization

*   **[This Index](documentation-index.md)**: The file you are currently reading.
*   **[Reorganization Plan](reorganization-plan.md)**: The detailed plan for restructuring and organizing all project documentation.
*   **[Consistency Check](CODE_DOCUMENTATION_CONSISTENCY_CHECK.md)**: A report on the consistency of documentation across the project.

### 3.4 External Analysis

*   **[AGI Assessment](../external-analysis/agi-assessment.md)**: A comprehensive assessment of the project's AGI level and future potential, based on its unique architecture.
*   **[Competitive Analysis](../external-analysis/competitive-analysis.md)**: A comparison of the Unified-AI-Project against other major AI systems and frameworks.
*   **[Frontend-Backend Comparison](../external-analysis/FRONTEND_BACKEND_COMPARISON.md)**: A document comparing the frontend and backend aspects of the project.

### 3.5 Philosophy

*   **[AGI Concepts](../philosophy/agi-concepts.md)**: A dive into the core philosophical ideas driving the project, such as the "Persistent Cognitive Loop" and the concept of a "Data Life."
*   **[Philosophy and Vision](../philosophy/PHILOSOPHY_AND_VISION.md)**: A document outlining the overall philosophy and vision of the project.

### 3.6 Archive

*   **[Archived Documents](../../09-archive/README.md)**: Contains historical documents that have been superseded but are kept for reference.
    *   `RESTRUCTURING_PLAN.md`

---
*Last Updated: 2025-08-10*