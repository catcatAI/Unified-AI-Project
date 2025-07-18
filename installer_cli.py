import sys
import yaml # Added
import os # Added

def get_os():
    if sys.platform.startswith("win"):
        return "windows"
    elif sys.platform.startswith("darwin"):
        return "macos"
    else:
        return "linux"

def main():
    try:
        print("Welcome to the Unified AI Project command-line installer.")
        print("This installer will guide you through the installation process.")
    except Exception as e:
        print(f"An error occurred: {e}")
    print("")

    # Load dependency configuration
    config_path = os.path.join(os.path.dirname(__file__), '..', 'dependency_config.yaml') # Adjusted path
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: dependency_config.yaml not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing dependency_config.yaml: {e}", file=sys.stderr)
        sys.exit(1)

    # Detect hardware and recommend configuration
    import psutil
    cpu_count = psutil.cpu_count()
    ram_gb = psutil.virtual_memory().total / (1024**3)
    if cpu_count <= 4 and ram_gb <= 8:
        recommended_hardware_config = "low"
    elif cpu_count <= 8 and ram_gb <= 16:
        recommended_hardware_config = "mid"
    else:
        recommended_hardware_config = "high"
    hardware_config = input(f"Hardware configuration (low/mid/high) [recommended: {recommended_hardware_config}]): ")
    if not hardware_config:
        hardware_config = recommended_hardware_config

    # Detect server and recommend configuration
    import socket
    try:
        socket.create_connection(("localhost", 8000), timeout=1)
        recommended_server_config = "local"
    except OSError:
        recommended_server_config = "none"
    server_config = input(f"Server configuration (none/local/remote) [recommended: {recommended_server_config}]): ")
    if not server_config:
        server_config = recommended_server_config

    # Get user input for configuration
    gemini_api_key = input("Gemini API Key: ")
    openai_api_key = input("OpenAI API Key: ")

    # Install dependencies
    print("Installing dependencies...")
    import subprocess

    # Prompt user for installation type
    print("\nAvailable installation types:")
    for install_type, details in config.get('installation', {}).items():
        print(f"  - {install_type}: {details.get('description', 'No description provided.')}")

    selected_type = input("Please choose an installation type (e.g., minimal, standard, full, ai_focused): ").strip().lower()

    install_packages = config.get('installation', {}).get(selected_type, {}).get('packages', [])

    if not install_packages:
        print(f"Warning: No packages found for installation type '{selected_type}'. Installing core dependencies only.", file=sys.stderr)
        # Fallback to core dependencies if selected type is invalid or has no packages
        install_packages = [dep['name'] for dep in config.get('dependencies', {}).get('core', [])]

    print(f"Installing packages for '{selected_type}' installation type...")
    for dependency in install_packages:
        try:
            print(f"  Installing {dependency}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
            print(f"  Successfully installed {dependency}.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing {dependency}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred while installing {dependency}: {e}", file=sys.stderr)

    # Create desktop shortcut
    print("Creating desktop shortcut...")
    from pyshortcuts import make_shortcut
    make_shortcut("installer_cli.py", name="Unified AI Project")

    print("Installation complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reconfigure":
        main()
    else:
        main()
