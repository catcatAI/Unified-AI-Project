# Value Types in the Unified AI Project

This document clarifies the different types of values used throughout this project: **Simulated**, **Actual**, and **Placeholder**. Understanding these distinctions is crucial for development, testing, and configuration.

## 1. Simulated Values

Simulated values are hardcoded or dynamically generated values used for development and testing purposes. They allow the application to run without access to real external services, APIs, or complex configurations. These are not intended for production use.

**Key Characteristics:**
- Found directly in the source code (`.py` files).
- Provide predictable, repeatable behavior for tests.
- Often represent a simplified version of what a real service would produce.

**Examples:**

- **Mock Service Responses:** In `apps/backend/src/services/vision_service.py`, the `analyze_image` method returns a hardcoded dictionary of analysis results, simulating the output of a real computer vision API.
  ```python
  # in VisionService.analyze_image()
  analysis_results["caption"] = "A mock image of a cat playing with a ball of yarn."
  ```

- **Dynamic Mock Data:** In `apps/backend/src/tools/image_generation_tool.py`, the `create_image` method generates a URL from a placeholder image service (`picsum.photos`) instead of calling a real image generation model.
  ```python
  # in ImageGenerationTool.create_image()
  placeholder_url = f"https://picsum.photos/seed/{seed}/600/400"
  ```

## 2. Actual Values

Actual values are the real, production-ready data that the application uses. They are typically loaded from external sources like configuration files or environment variables, keeping sensitive information out of the source code.

**Key Characteristics:**
- Loaded from `.yaml` or `.json` configuration files, or from environment variables.
- Represent real-world settings, API keys, and other sensitive data.
- The system is designed to use these values in a production environment.

**Examples:**

- **API Keys:** In `apps/backend/configs/api_keys.yaml`, values like `GEMINI_API_KEY_PLACEHOLDER` are designed to be replaced by actual API keys loaded from environment variables at runtime.

- **Application Configuration:** In `apps/backend/configs/config.yaml`, settings like `log_level` and `environment` control the application's behavior and are considered actual values.

## 3. Placeholder Values

Placeholder values are markers in the code or configuration that indicate something is incomplete, needs to be implemented, or requires a specific value to be provided.

**Key Characteristics:**
- Can be found in source code as comments (`//TODO`), `NotImplementedError` exceptions, or as specific placeholder strings in configuration files.
- Signal areas for future development or required configuration.

**Examples:**

- **TODO Comments:** The project uses a specific format for `TODO` comments, like `TODO(type): description`, to mark areas that need implementation. The `apps/backend/scan_placeholders.py` script is designed to find these.

- **`NotImplementedError`:** In base classes like `apps/backend/src/core_ai/meta_formulas/meta_formula.py`, this error correctly indicates that a method must be implemented by subclasses.

- **Configuration Placeholders:** In `apps/backend/configs/api_keys.yaml`, strings like `GEMINI_API_KEY_PLACEHOLDER` are placeholders that the system expects to be replaced by actual values from the environment.
