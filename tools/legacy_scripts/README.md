# Legacy Scripts Archive

This directory contains older installation and launch scripts that have been formalized into the `core.system.bootstrap` module.

## Contents
- `auto_install.py`: Original automated installer.
- `install_angela.py`: Hardware-aware tiering installer.
- `Launcher.bat`: Original Windows launcher.
- `launch_angela.bat`: Backend REPL launcher.
- `create_shortcuts.bat`: Windows shortcut utility.
- `auto_install_and_start.sh`: Linux one-click script.
- `install_no_sudo.py`: Non-privileged installer variant.

## Why move them?
To reduce root-level noise and ensure the project follows a single, formalized initialization path via `pnpm setup` and `pnpm start` (which internally use `core.system.bootstrap`).

**DO NOT** use these scripts for new development. Use the formalized bootstrap system instead.
