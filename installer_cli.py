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

    # --- Genesis Process for First Time Setup ---
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_path = os.path.join(project_root, '.env')
    if not os.path.exists(env_path) or "MIKO_HAM_KEY" not in open(env_path).read():
        print("\n--- First Time Setup: Generating AI Identity ---")
        from src.core_ai.genesis import GenesisManager
        genesis_secret, uid = GenesisManager.create_genesis_secret()
        shards = GenesisManager.split_secret_into_shards(genesis_secret)

        print("A unique identity (UID and Encryption Key) has been generated for your AI.")
        print("This identity is split into 3 'Shards'. You must back up AT LEAST TWO of them to a safe, separate location.")
        print("Losing two or more shards will result in PERMANENT data loss.\n")

        for i, shard in enumerate(shards):
            print(f"--- SHARD {i+1} (Save this!) ---")
            print(shard)
            print("-" * (len(shard)))

        input("\nPlease confirm you have backed up at least two shards, then press Enter to continue...")

        # Save UID and HAM Key to .env file
        recovered_secret = GenesisManager.recover_secret_from_shards(shards)
        parsed_uid, ham_key = GenesisManager.parse_genesis_secret(recovered_secret)

        with open(env_path, 'a') as f:
            f.write(f"\nUID={parsed_uid}")
            f.write(f"\nMIKO_HAM_KEY={ham_key}\n")
        print("Identity saved to .env file.")


    # Install dependencies
    print("Installing dependencies...")
    import subprocess

    # Prompt user for installation type
    print("\nAvailable installation types:")
    for install_type, details in config.get('installation', {}).items():
        print(f"  - {install_type}: {details.get('description', 'No description provided.')}")

    selected_type = input("Please choose an installation type (e.g., minimal, standard, full, ai_focused, game): ").strip().lower()

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

    # Save Python executable path to .env file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_path = os.path.join(project_root, '.env')
    try:
        with open(env_path, 'a') as f:
            f.write(f"\nPYTHON_EXECUTABLE={sys.executable}\n")
        print(f"Python executable path saved to {env_path}")
    except Exception as e:
        print(f"Error saving Python executable path: {e}", file=sys.stderr)

    print("Installation complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reconfigure":
        main()
    else:
        main()
