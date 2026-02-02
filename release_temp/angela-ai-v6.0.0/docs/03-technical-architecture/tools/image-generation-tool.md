# ImageGenerationTool: Generating Images from Text Prompts

## Overview

This document provides an overview of the `ImageGenerationTool` module (`src/tools/image_generation_tool.py`). Its primary function is to provide the AI with the capability to generate images based on textual descriptions.

This tool is a key component for creative tasks, content generation, and providing visual aids in response to user requests. It allows the AI to translate conceptual or descriptive text into a visual representation.

## Key Responsibilities and Features

*   **Initialization (`__init__`)**: Initializes the tool with an optional configuration. In a full implementation, this would involve setting up API keys and other parameters for a real image generation service.
*   **Image Creation (`create_image`)**: The core method of the tool. It takes a `prompt` (a string describing the desired image) and an optional `style` (e.g., `"photorealistic"`, `"cartoon"`, `"abstract"`) and returns a dictionary containing the result.
*   **Placeholder Implementation**: The current version of this tool is a placeholder. It does not call a real image generation API (like DALL-E, Midjourney, or Stable Diffusion). Instead, it generates a static, seeded placeholder image URL from `picsum.photos`. This provides a consistent and predictable visual output for a given prompt during development and testing.

## How it Works

The tool receives a text prompt and a style. It uses a simple hashing function on the prompt string to generate a consistent seed. This seed is then used to construct a URL for `picsum.photos`, which serves a unique but deterministic placeholder image for that seed. The tool returns a dictionary containing the URL of this placeholder image and some descriptive alt text, which includes the original prompt and style.

## Integration with Other Modules

*   **`ToolDispatcher`**: This tool is designed to be invoked by the `ToolDispatcher` when the AI's intent is to create an image. The `ToolDispatcher` would extract the `prompt` and `style` from the user's query and pass them to this tool.
*   **`ImageGenerationAgent`**: A specialized agent could be built around this tool to handle more complex image generation requests, manage a gallery of generated images, or refine prompts based on user feedback.

## Code Location

`src/tools/image_generation_tool.py`