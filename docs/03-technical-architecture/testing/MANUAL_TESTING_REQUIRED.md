# Manual Testing Required

This document lists tasks that require manual testing due to limitations in the automated execution environment.

## Task 1: Verify HSP Connection Reliability Fix

- **Date**: 2025-08-10
- **File Modified**: `apps/backend/src/hsp/connector.py`
- **Change Description**: Implemented a connection retry mechanism in the `connect` method of the `HSPConnector` class.

### Reason for Manual Test

The automated `run_shell_command` tool is currently unable to execute tests within the `Unified-AI-Project` directory, returning the error: `Directory 'Unified-AI-Project' is not a registered workspace directory.`

### Testing Steps

1.  Navigate to the `Unified-AI-Project` directory in your terminal.
2.  Run the full test suite using the command: `pnpm test`.
3.  Specifically, check the results for `test_hsp_integration.py`.
4.  **Expected Outcome**: The tests in `test_hsp_integration.py`, which were previously failing according to the project's roadmap, should now pass. The improved connection logic in `HSPConnector` should resolve the instability issues.
