# Time System

## Overview

The `TimeSystem` (`src/core_ai/time_system.py`) is a fundamental component within the Unified-AI-Project that provides the AI (Angela) with a **sense of time and the ability to incorporate temporal context** into her interactions and decision-making. While seemingly simple, accurate time awareness is crucial for an AI to behave naturally, schedule tasks, and respond appropriately to time-sensitive queries.

This module allows Angela to understand concepts like "morning," "afternoon," and "tonight," and to manage reminders and time-based events.

## Key Responsibilities and Features

1.  **Current Time Retrieval (`get_current_time`, `get_formatted_current_time`)**:
    *   Provides the current date and time, either as a `datetime` object or a formatted string.
    *   Includes a `current_time_override` for testing or specific scenarios where the system's perceived time needs to be manipulated (e.g., simulating different times of day).

2.  **Time-of-Day Segmentation (`get_time_of_day_segment`)**:
    *   Categorizes the current hour into logical segments like "morning," "afternoon," "evening," or "night."
    *   This allows Angela to tailor her greetings and responses based on the time of day, enhancing the naturalness of interactions.

3.  **Reminder Management (Placeholder)**:
    *   Includes placeholder methods (`set_reminder`, `check_due_reminders`) for future implementation of a full-fledged reminder system.
    *   This indicates a planned capability for the AI to manage and act upon scheduled events.

## How it Works

The `TimeSystem` primarily wraps Python's `datetime` module, providing a consistent interface for time-related queries. Its `get_time_of_day_segment` method uses simple hour-based logic to categorize the time. The `current_time_override` allows for flexible testing and simulation of time-dependent behaviors without altering the system clock.

## Integration with Other Modules

-   **`DialogueManager`**: Uses the `TimeSystem` to generate time-appropriate greetings and to understand temporal references in user queries.
-   **`ProjectCoordinator`**: Could potentially use the `TimeSystem` for scheduling tasks, setting deadlines, or managing time-sensitive project phases.
-   **`EmotionSystem`**: The time of day might influence Angela's emotional state or energy levels, creating more dynamic and realistic behavior.
-   **`HAMMemoryManager`**: Events and memories stored in HAM are timestamped, and the `TimeSystem` provides the canonical time source for these timestamps.

## Code Location

`src/core_ai/time_system.py`