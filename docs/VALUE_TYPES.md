# Value Types in the Unified AI Project

This document clarifies the different types of values used throughout this project: **Simulated**, **Actual**, and **Placeholder**. Understanding these distinctions is crucial for development, testing, and configuration.

## 1. Simulated Values

Simulated values are hardcoded or dynamically generated values used for development and testing purposes. They allow the application to run without access to real external services, APIs, or complex configurations. These are not intended for production use.

### Backend (`apps/backend`)

- **Mock Service Responses:** In `apps/backend/src/services/vision_service.py`, the `analyze_image` method returns a dynamically generated dictionary of analysis results, simulating the output of a real computer vision API.
- **Dynamic Mock Data:** In `apps/backend/src/tools/image_generation_tool.py`, the `create_image` method generates a URL from a placeholder image service (`picsum.photos`) instead of calling a real image generation model.

### Frontend (`apps/frontend-dashboard`)

- **Fallback Mock Data:** In `apps/frontend-dashboard/src/lib/api.ts`, functions like `getSystemStatus`, `getServiceHealth`, and `getSystemMetrics` return hardcoded mock data when the corresponding API calls fail.
- **Component-Level Mock Data:** In `apps/frontend-dashboard/src/components/ai-dashboard/tabs/dashboard-overview.tsx`, the `stats`, `systems`, and `recentActivity` arrays are initialized with hardcoded mock data.

### Desktop App (`apps/desktop-app`)

- **Mock API Implementations:** In `apps/desktop-app/electron_app/src/api/codeAnalysis.ts`, the `uploadProjectForAnalysis` and `getAnalysisResult` functions are mock implementations that return hardcoded data after a timeout.

## 2. Actual Values

Actual values are the real, production-ready data that the application uses. They are typically loaded from external sources like configuration files or environment variables, keeping sensitive information out of the source code.

### Backend (`apps/backend`)

- **API Keys:** In `apps/backend/configs/api_keys.yaml`, values like `GEMINI_API_KEY_PLACEHOLDER` are designed to be replaced by actual API keys loaded from environment variables at runtime.
- **Application Configuration:** In `apps/backend/configs/config.yaml`, settings like `log_level` and `environment` control the application's behavior and are considered actual values.

### Frontend (`apps/frontend-dashboard`)

- **API Base URL:** In `apps/frontend-dashboard/src/lib/api.ts`, the `API_BASE_URL` is determined by the `NODE_ENV` environment variable, which is an actual value that changes depending on the environment.
- **API Response Data:** The data returned from successful API calls to the backend are considered actual values.

## 3. Placeholder Values

Placeholder values are markers in the code or configuration that indicate something is incomplete, needs to be implemented, or requires a specific value to be provided.

### Backend (`apps/backend`)

- **TODO Comments:** The project uses a specific format for `TODO` comments, like `TODO(type): description`, to mark areas that need implementation. The `apps/backend/scan_placeholders.py` script is designed to find these.
- **`NotImplementedError`:** In base classes like `apps/backend/src/core_ai/meta_formulas/meta_formula.py`, this error correctly indicates that a method must be implemented by subclasses.
- **Configuration Placeholders:** In `apps/backend/configs/api_keys.yaml`, strings like `GEMINI_API_KEY_PLACEHOLDER` are placeholders that the system expects to be replaced by actual values from the environment.
- **Placeholder Logic Comments:** In files like `apps/backend/src/core_ai/agent_manager.py`, comments like `# This is a placeholder for a more robust health check mechanism.` indicate areas for future improvement.

### Frontend & Desktop

- **UI Placeholders:** In the React components, the `placeholder` attribute of input fields (e.g., `<Input placeholder="Search..." />`) is a placeholder for user input.
- **Placeholder Comments:** In files like `apps/desktop-app/electron_app/src/api/codeAnalysis.ts`, comments like `// Placeholder for Code Analysis API service` indicate that the file contains a mock implementation.
