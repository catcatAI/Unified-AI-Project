import sys

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
    dependencies = ["psutil", "beautifulsoup4", "scikit-image", "SpeechRecognition", "transformers", "PyGithub", "aiounittest"]
    for dependency in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])
        except subprocess.CalledProcessError as e:
            print(f"Error installing {dependency}: {e}")

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
