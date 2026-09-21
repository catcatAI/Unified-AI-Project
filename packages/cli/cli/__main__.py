#!/usr/bin/env python3
"""`python -m cli` entry — delegates to unified_cli.main (R76 fix).

The previous __main__ imported cli.cli_runner, which has never existed
inside the cli package (a stray copy lives at packages/cli/cli_runner.py,
outside the installed package) and crashed at startup.
"""
from .unified_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
