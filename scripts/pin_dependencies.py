import subprocess
import os
import sys

def pin_dependencies():
    """
    Generates a pinned requirements.txt file from pyproject.toml using pip-compile.

    This script compiles all dependencies, including optional groups specified,
    into a single requirements.txt file with pinned versions. This is useful for
    creating reproducible environments for CI/CD and production.
    """
    print("Starting dependency pinning process...")

    # Get the project root directory, assuming this script is in the 'scripts' folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    backend_dir = os.path.join(project_root, 'packages', 'backend')
    pyproject_toml_path = os.path.join(backend_dir, 'pyproject.toml')
    requirements_txt_path = os.path.join(backend_dir, 'requirements.txt')

    if not os.path.exists(pyproject_toml_path):
        print(f"Error: pyproject.toml not found at {pyproject_toml_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Source: {pyproject_toml_path}")
    print(f"Output: {requirements_txt_path}")

    # We specify the 'dev' extra, which includes all other optional dependencies.
    # This creates a comprehensive lock file for the development environment.
    command = [
        sys.executable,
        "-m",
        "piptools",
        "compile",
        "--extra=dev",
        f"--output-file={requirements_txt_path}",
        pyproject_toml_path,
        "--quiet" # Adding quiet to reduce noise, will still show errors.
    ]

    print("Running pip-compile...")
    try:
        # We need to run this command from the backend directory so that the
        # editable mode reference "unified-ai-project[...]" is resolved correctly.
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=backend_dir
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"\nSuccessfully pinned dependencies to {requirements_txt_path}")
    except subprocess.CalledProcessError as e:
        print("Error running pip-compile:", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'pip-tools' not found.", file=sys.stderr)
        print("Please ensure you have installed the dev dependencies with:", file=sys.stderr)
        print("pip install -e .[dev]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    pin_dependencies()
