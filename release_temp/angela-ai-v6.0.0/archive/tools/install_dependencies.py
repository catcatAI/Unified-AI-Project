import subprocess
import os
import sys

def run_pnpm_install(project_root):
    print(f"Running pnpm install in {project_root}")
    try:
        # Use shell=True for Windows to find pnpm in PATH
        result = subprocess.run(
            ["pnpm", "install"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("pnpm install completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running pnpm install: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: pnpm command not found. Please ensure pnpm is installed and in your PATH.")
        return False

if __name__ == "__main__":
    # Assuming this script is in D:\Projects\Unified-AI-Project\tools
    # and the project root is D:\Projects\Unified-AI-Project
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))

    if not run_pnpm_install(project_root):
        sys.exit(1)
