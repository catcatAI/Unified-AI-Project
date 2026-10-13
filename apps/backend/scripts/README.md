# `apps/backend/scripts/` — helper scripts

Utility scripts that run against the backend. All are invoked directly with the
project interpreter; none of them is wired into `package.json`.

```bash
.venv/bin/python apps/backend/scripts/<script>.py
```

> **History:** this directory used to host an "auto-fix system"
> (`simple_auto_fix.py`, `auto_fix_complete.py`, `advanced_auto_fix.py`,
> `enhanced_auto_fix.py`, `runtime_auto_fix.py`, `smart_auto_fix.py`,
> `auto_fix_imports.py`, plus the `auto_fix.sh` / `auto_fix.bat` menu wrappers
> and their `pnpm fix:*` aliases). Those were deliberately removed in v6.0.4
> ("清理自动修复系统") and must not be re-introduced: the `core_ai` → `ai`
> import migration they performed is finished, and the imported paths they
> rewrote no longer exist.

## Analysis and error triage

| Script                   | Purpose                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| `analyze_failures.py`    | Analyse test failures from the latest `test_results.json`.        |
| `error_analyzer.py`      | Standalone error-analysis module used by the triage tooling.      |
| `execute_smart_fix.py`   | Apply a smart fix plan produced by the analysers.                 |
| `fix_executor.py`        | Standalone fix-execution module.                                  |
| `integration_fixer.py`   | Check for integration problems and repair them.                   |
| `smart_dev_runner.py`    | Start the dev server, detecting and fixing errors on the way up.  |
| `smart_executor.py`      | Run a command, detect failures, and hand them to the fix tooling. |
| `workflow_controller.py` | Drive the fix/verify workflow stages.                             |
| `final_validation.py`    | End-to-end validation of the import-health checks.                |

## Test coverage

| Script                      | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| `coverage_analyzer.py`      | Test-coverage analyser.                    |
| `coverage_monitor.py`       | Test-coverage monitor (repeated sampling). |
| `test_result_visualizer.py` | Render test results for inspection.        |

## Performance

| Script                               | Purpose                                        |
| ------------------------------------ | ---------------------------------------------- |
| `benchmark_baseline.py`              | Benchmark baseline runner.                     |
| `performance_benchmark_framework.py` | Performance benchmark framework.               |
| `performance_benchmark_workflow.py`  | Benchmark + regression-detection workflow.     |
| `performance_regression_detector.py` | Compare runs and flag performance regressions. |
| `profiler.py`                        | Unified profiling entry point.                 |

## Operations

| Script                    | Purpose                                                    |
| ------------------------- | ---------------------------------------------------------- |
| `clean_old_backups.py`    | Delete backup directories older than the retention period. |
| `manage_backup_dirs.py`   | Backup-directory management.                               |
| `health_check_service.py` | Quick and full health checks.                              |
| `export_openapi.py`       | Export the OpenAPI spec from the **production** app.       |

## Experiments

| Script                                    | Purpose                                                          |
| ----------------------------------------- | ---------------------------------------------------------------- |
| `unified_engine_principle_experiments.py` | Reproducible unified-engine principle experiments.               |
| `start_separate_terminals.ps1`            | Windows helper that launches the dev services, one per terminal. |

## Related documents

- `TEST_RESULT_PROCESSING_README.md` /
  `TEST_RESULT_PROCESSING_INTEGRATION_GUIDE.md` — test-result processing
  pipeline.
- `README_separated_test_fix.md` — separated test-fix workflow.
- `../ACTIVE_SCRIPTS.md`-style indexes for the repo-root `scripts/` directory
  live at `scripts/ACTIVE_SCRIPTS.md`.
