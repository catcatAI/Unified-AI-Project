# Horizontal Alignment Roadmap

This document outlines a prioritized roadmap for horizontally aligning the sub-projects within this monorepo. The goal is to create a more unified and consistent developer experience and final product.

## Phase 1: Foundational Improvements

1.  **Centralize Dependency Management**:
    *   **Goal**: Migrate all sub-projects to use a single, centralized dependency management system. This will ensure that all sub-projects are using the same versions of shared dependencies and will simplify the process of updating dependencies.
    *   **Proposed Solution**: Use `pnpm` workspaces to manage all dependencies. This will allow us to define all dependencies in a single `package.json` file at the root of the monorepo.
    *   **Priority**: High

2.  **Unify Code Style and Linting**:
    *   **Goal**: Establish a consistent code style and linting rules for all sub-projects.
    *   **Proposed Solution**: Create a shared ESLint configuration that can be extended by each sub-project. This will ensure that all code is written in a consistent style and will help to prevent common errors.
    *   **Priority**: High

## Phase 2: Codebase Integration

1.  **Integrate "Quest Features" into the `frontend-dashboard`**:
    *   **Goal**: Migrate the routes and components from the `quest-features` application into the main Next.js application.
    *   **Proposed Solution**: Create new pages in the `frontend-dashboard`'s `src/app` directory for each of the routes in the `quest-features` application. The existing components can be moved to the `src/components` directory and reused.
    *   **Priority**: Medium

2.  **Extract Shared Components into a Shared Library**:
    *   **Goal**: Identify components that are being re-implemented in multiple sub-projects and extract them into a shared library.
    *   **Proposed Solution**: Create a new `packages/ui` directory that will contain a shared UI component library. This library can then be used by all of the sub-projects.
    *   **Priority**: Medium

## Phase 3: Build and Test Processes

1.  **Create a Unified Build Process**:
    *   **Goal**: Create a unified set of scripts for building all of the sub-projects.
    *   **Proposed Solution**: Create a new `scripts` directory at the root of the monorepo that will contain scripts for building each of the sub-projects. These scripts can then be called from the root `package.json` file.
    *   **Priority**: Low

2.  **Create a Unified Test Process**:
    *   **Goal**: Create a unified set of scripts for testing all of the sub-projects.
    *   **Proposed Solution**: Create a new `scripts` directory at the root of the monorepo that will contain scripts for testing each of the sub-projects. These scripts can then be called from the root `package.json` file.
    *   **Priority**: Low
