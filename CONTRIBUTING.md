# Contributing to Unified-AI-Project

First off, thank you for considering contributing to Unified-AI-Project! It's
people like you that make open source such a great community.

## Where to Start?

Not sure where to start? You can:

- Check out the
  [open issues](https://github.com/your-username/Unified-AI-Project/issues)
- Read through our extensive [documentation](./docs/README.md) to understand the
  project's philosophy, architecture, and game design.

## Development Workflow

1.  **Fork the repository** and create your branch from `main`.
2.  **Make your changes**.
3.  **Add or update tests** for your changes. We use `pytest` for our Python
    tests.
    - For game-related changes, please add tests to the `tests/game/` directory.
4.  **Ensure all tests pass** by running `pytest` in the root directory.
5.  **Format your code**. We use `black` for Python code formatting.
6.  **Create a pull request**.

## Code Style

- **Python**: We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/)
  style guide.
- **JavaScript/TypeScript**: We follow standard community practices, and use
  `prettier` for consistent formatting.
- **Internal Data Structures**: Please follow the standards outlined in
  `docs/technical_design/INTERNAL_DATA_STANDARDS.md`.

## Game Module Contributions

When contributing to the game module (`src/game/`), please keep the following in
mind:

- **Design Documents**: Before implementing new features, please check the
  relevant design documents in `docs/game/`. If you are proposing a new feature,
  please create or update a design document first.
- **Asset Licenses**: If you are adding new art assets, please ensure they are
  licensed under a compatible open-source license (e.g., CC0, CC-BY) and add the
  license information to `src/game/assets/metadata.md`.
- **Testing**: All new game logic should be accompanied by corresponding unit
  tests in the `tests/game/` directory.

Thank you for your contributions!
