#!/usr/bin/env python3
"""`python -m cli` entry — delegates to unified_cli.main (R76 fix).

The previous __main__ imported cli.cli_runner, which has never existed
inside the cli package and crashed at startup. (The stray
packages/cli/cli_runner.py copy that used to sit outside the package was
since removed in the R76 purge.)
"""

from .unified_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
