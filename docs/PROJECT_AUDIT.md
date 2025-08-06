# Project Audit

This document contains a comprehensive audit of the Unified AI Project, including a feature inventory and a list of identified issues such as errors, code duplication, and integration problems.

## Feature Inventory

### Backend (`apps/backend`)

#### `apps/backend/src/core_ai/agent_manager.py`
- Manages the lifecycle of sub-agents.
- Can launch and terminate sub-agent processes.
- Discovers available agent scripts automatically.
- Can wait for an agent to be ready by checking for its capability advertisement.

- **Hardcoded Path:** The `_discover_agent_scripts` method has a hardcoded path to the `src/agents` directory. It would be better to make this configurable.

#### `apps/backend/src/core_ai/crisis_system.py`
- **Simplified Sentiment Analysis:** The sentiment analysis is very basic and only checks for a few negative words. It could be easily fooled.
- **Hardcoded Negative Words:** The list of negative words is hardcoded in the `assess_input_for_crisis` method. It would be better to move this to the configuration file.
- **Noisy `print` Statements:** The code uses `print` statements for logging. It would be better to use the `logging` module consistently.
- **Hardcoded Log File Name:** The `_trigger_protocol` method has a hardcoded log file name `crisis_log.txt`. It would be better to make this configurable.
- **Lack of De-escalation Logic:** The comment in `assess_input_for_crisis` mentions that "More sophisticated logic could allow assess_input to also de-escalate." This is a potential area for improvement.

- **Lack of De-escalation Logic:** The comment in `assess_input_for_crisis` mentions that "More sophisticated logic could allow assess_input to also de-escalate." This is a potential area for improvement.

#### `apps/backend/src/core_ai/dialogue/dialogue_manager.py`
- **Incomplete Session Management:** The `active_sessions` dictionary is now being populated, but the conversation history is never actually used. The `get_simple_response` method does not take the history into account when generating a response.
- **Noisy `print` Statements:** The code still uses a `print` statement in `start_session`. This should be replaced with a `logging` call.
- **Lack of Context in Tool Dispatch:** The `tool_dispatcher.dispatch` call does not pass any conversation context. This means that the tools are stateless and cannot take the conversation history into account.

*This section will be populated as the audit progresses.*

## Identified Issues

### Backend (`apps/backend`)

#### `apps/backend/src/core_ai/agent_manager.py`
- **Placeholder `check_agent_health`:** The `check_agent_health` method is a placeholder and only checks if the process is running. This is not a robust health check.
- **Placeholder `wait_for_agent_ready`:** The `wait_for_agent_ready` method is also a placeholder. It relies on the `ServiceDiscoveryModule` to check for capability advertisements, which might not be reliable.
- **Noisy `print` Statements:** The code uses `print` statements for logging. It would be better to use the `logging` module consistently.
- **Potential Race Condition:** In `launch_agent`, there is a potential race condition. The code checks if an agent is already running and then launches it. It's possible that another process could launch the same agent in between these two steps.
- **Hardcoded Path:** The `_discover_agent_scripts` method has a hardcoded path to the `src/agents` directory. It would be better to make this configurable.

*This section will be populated as the audit progresses.*
