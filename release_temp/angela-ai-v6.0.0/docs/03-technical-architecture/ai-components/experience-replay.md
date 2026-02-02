# ExperienceReplayBuffer: AI Learning from Past Experiences

## Overview

This document provides an overview of the `ExperienceReplayBuffer` module, located at `apps/backend/src/core_ai/learning/experience_replay.py`. This module is a key component of the continuous learning framework.

## Purpose

The primary purpose of the `ExperienceReplayBuffer` is to store the AI's experiences (a collection of states, actions, rewards, and outcomes) and allow for prioritized sampling of this data. This mechanism helps break the correlation between consecutive experiences, leading to more stable and efficient learning for reinforcement learning models.

## Key Responsibilities and Features

*   **Experience Storage**: The buffer stores a collection of experiences up to a defined `capacity`.
*   **Prioritized Replay**: Instead of uniform random sampling, the buffer uses a priority system (controlled by `priority_alpha`) to increase the probability of sampling more "important" or "surprising" experiences. This is based on a calculated priority for each experience.
*   **Priority Calculation (`_calculate_priority`)**: The priority of an experience is calculated based on its contents. Currently, experiences that result in an error are given a higher priority, but this is a placeholder for more sophisticated calculations (e.g., based on Temporal-Difference error).
*   **Batch Sampling (`sample_batch`)**: Provides a method to sample a batch of experiences based on their calculated priorities. This batch can then be used to train or fine-tune AI models.

## How it Works

When a new experience is added via `add_experience`, it is stored in a buffer. A priority score is calculated for this experience. When a model needs to be trained, it can call `sample_batch` to retrieve a list of experiences. The sampling process is weighted by the priority scores, meaning experiences that are considered more informative for learning are more likely to be selected.

## Integration with Other Modules

*   **`LearningManager`**: The `LearningManager` would be the primary user of this buffer, adding new experiences as the AI interacts with its environment and sampling batches to train its internal models.
*   **Reinforcement Learning Models**: Any RL model within the AI system would consume the batches sampled from this buffer for its training cycles.

## Code Location

`apps/backend/src/core_ai/learning/experience_replay.py`