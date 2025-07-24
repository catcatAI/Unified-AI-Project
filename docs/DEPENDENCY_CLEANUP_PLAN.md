# Dependency Cleanup Plan

This document outlines a plan for cleaning up and organizing the dependencies of the Unified AI Project.

## 1. Missing Dependencies

The following dependencies are imported in the code but are not defined in `dependency_config.yaml` or `pyproject.toml`.

-   **`aiounittest`**: Add to the `testing` group in `dependency_config.yaml`.
-   **`amqtt`**: Add as a fallback for `paho-mqtt` in `dependency_config.yaml`.
-   **`beautifulsoup4`**: The `bs4` import comes from the `beautifulsoup4` package. Add this to the `optional` dependencies in `dependency_config.yaml` under a new `web_scraping` feature.
-   **`github3.py`**: The `github` import likely comes from the `github3.py` package. Add this to the `optional` dependencies in `dependency_config.yaml` under a new `integrations` feature.
-   **`gmqtt`**: Add as a fallback for `paho-mqtt` in `dependency_config.yaml`.
-   **`huggingface-hub`**: This is a dependency of `sentence-transformers`. It should be added to the `ai_focused` installation group in `dependency_config.yaml`.
-   **`pandas`**: Move from an optional to a core dependency in `dependency_config.yaml`.
-   **`pytest`**: Add to the `testing` group in `dependency_config.yaml`.
-   **`scikit-image`**: The `skimage` import comes from the `scikit-image` package. Add this to the `optional` dependencies in `dependency_config.yaml` under a new `image_processing` feature.
-   **`scikit-learn`**: The `sklearn` import comes from the `scikit-learn` package. Move from an optional to a core dependency in `dependency_config.yaml`.
-   **`SpeechRecognition`**: Add to the `optional` dependencies in `dependency_config.yaml` under a new `audio` feature.
-   **`transformers`**: This is a dependency of `sentence-transformers`. It should be added to the `ai_focused` installation group in `dependency_config.yaml`.

## 2. Unused Dependencies

The following dependencies are defined in `dependency_config.yaml` or `pyproject.toml` but are not imported anywhere in the code.

-   **`langchain`**: Remove from `dependency_config.yaml`.

## 3. Dependency Name Normalization

The following dependencies have a mismatch between their package name and their import name. I will update `dependency_config.yaml` and `scripts/compare_imports.py` to use the correct names.

-   `faiss-cpu` -> `faiss`
-   `paho-mqtt` -> `paho`
-   `pytest-asyncio` -> `pytest_asyncio`
-   `python-dotenv` -> `dotenv`
-   `PyYAML` -> `yaml`
-   `secret-sharing` -> `secretsharing`

## 4. Recategorization of Dependencies

-   Move `pandas` and `scikit-learn` to the `core` dependencies in `dependency_config.yaml` as they seem to be used in core functionalities.
-   Create new feature groups in `dependency_config.yaml` for `web_scraping`, `integrations`, `image_processing`, and `audio` to better organize the optional dependencies.

By implementing these changes, we can ensure that the project's dependencies are well-organized, consistent, and accurately reflect the project's needs.
