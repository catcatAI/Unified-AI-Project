# Angela AI MOD Tier Configuration

This directory is reserved for non-standard extensions, third-party plugins, and experimental capabilities.

## Structure
- `active_mods.default.yaml`: List of mods enabled by default.
- `active_mods.user.yaml`: User-defined mod list and parameters.
- `active_mods.evolved.yaml`: Angela's learned adjustments to mod parameters.
- `sample_mod/`: Directory structure for a standalone mod.

## How to use
Add your mod configuration files here. The system will automatically detect and merge them into the `mods` tier if referenced in `active_mods`.
