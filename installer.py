import sys
import yaml # Added
import os # Added
from PyQt5.QtWidgets import QApplication, QWizard, QWizardPage

class InstallationWizard(QWizard):
    def __init__(self):
        super().__init__()

        # Load dependency configuration
        config_path = os.path.join(os.path.dirname(__file__), 'dependency_config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.dependency_config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: dependency_config.yaml not found at {config_path}", file=sys.stderr)
            self.dependency_config = {} # Fallback to empty config
        except yaml.YAMLError as e:
            print(f"Error parsing dependency_config.yaml: {e}", file=sys.stderr)
            self.dependency_config = {} # Fallback to empty config

        self.addPage(WelcomePage())
        self.addPage(ConfigurationPage())
        self.addPage(APIKeyPage())
        self.addPage(InstallationPage())
        self.addPage(FinishedPage())

        self.setWindowTitle("Installation Wizard")
        self.selected_installation_type = None # Added to store the selected type

    def get_os(self):
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("darwin"):
            return "macos"
        else:
            return "linux"

from PyQt5.QtWidgets import QLabel

class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Welcome to the Unified AI Project installation wizard."))
        self.setLayout(layout)

from PyQt5.QtWidgets import QRadioButton, QGroupBox, QVBoxLayout, QComboBox, QLabel

class ConfigurationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Configuration")

        layout = QVBoxLayout()

        # Installation Type configuration
        install_type_group = QGroupBox("Installation Type")
        install_type_layout = QVBoxLayout()
        self.install_type_combo = QComboBox()
        
        # Populate combo box from dependency_config.yaml
        installation_types = self.wizard().dependency_config.get('installation', {})
        for install_type, details in installation_types.items():
            self.install_type_combo.addItem(f"{install_type} ({details.get('description', '')})", install_type)
        
        install_type_layout.addWidget(QLabel("Select the desired installation type:"))
        install_type_layout.addWidget(self.install_type_combo)
        install_type_group.setLayout(install_type_layout)
        layout.addWidget(install_type_group)

        # Connect signal to update wizard's selected_installation_type
        self.install_type_combo.currentIndexChanged.connect(self._update_selected_type)

        # Hardware configuration
        hardware_group = QGroupBox("Hardware Configuration")
        hardware_layout = QVBoxLayout()
        self.low_end_hardware_radio = QRadioButton("Low-end hardware")
        self.mid_range_hardware_radio = QRadioButton("Mid-range hardware")
        self.high_end_hardware_radio = QRadioButton("High-end hardware")
        hardware_layout.addWidget(self.low_end_hardware_radio)
        hardware_layout.addWidget(self.mid_range_hardware_radio)
        hardware_layout.addWidget(self.high_end_hardware_radio)
        hardware_group.setLayout(hardware_layout)
        layout.addWidget(hardware_group)

        # Server configuration
        server_group = QGroupBox("Server Configuration")
        server_layout = QVBoxLayout()
        self.no_server_radio = QRadioButton("No server")
        self.local_server_radio = QRadioButton("Local server")
        self.remote_server_radio = QRadioButton("Remote server")
        server_layout.addWidget(self.no_server_radio)
        server_layout.addWidget(self.local_server_radio)
        server_layout.addWidget(self.remote_server_radio)
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)

        self.setLayout(layout)

    def _update_selected_type(self):
        self.wizard().selected_installation_type = self.install_type_combo.currentData()

    def initializePage(self):
        # Set default selection if not already set
        if not self.wizard().selected_installation_type and self.install_type_combo.count() > 0:
            self.install_type_combo.setCurrentIndex(0)
            self._update_selected_type()

from PyQt5.QtWidgets import QProgressBar

class InstallationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Installation")
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def initializePage(self):
        self.progress_bar.setValue(0)
        self.wizard().nextButton.setEnabled(False)
        import threading
        thread = threading.Thread(target=self.install_dependencies)
        thread.start()

    def install_dependencies(self):
        import subprocess
        import sys

        def install(package):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], timeout=300)
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")
            except subprocess.TimeoutExpired as e:
                print(f"Timeout installing {package}: {e}")

        selected_type = self.wizard().selected_installation_type
        config = self.wizard().dependency_config

        if selected_type and config:
            dependencies_to_install = config.get('installation', {}).get(selected_type, {}).get('packages', [])
        else:
            # Fallback to core dependencies if no type selected or config not loaded
            dependencies_to_install = [dep['name'] for dep in config.get('dependencies', {}).get('core', [])]
            print("Warning: No installation type selected or config not loaded. Installing core dependencies only.", file=sys.stderr)

        if not dependencies_to_install:
            print("No dependencies to install for the selected type.", file=sys.stderr)
            self.progress_bar.setValue(100)
            self.wizard().nextButton.setEnabled(True)
            return

        for i, dependency in enumerate(dependencies_to_install):
            install(dependency)
            self.progress_bar.setValue(int((i + 1) / len(dependencies_to_install) * 100))

        self.create_shortcut()
        self.wizard().nextButton.setEnabled(True)

    def detect_hardware(self):
        import psutil

        cpu_count = psutil.cpu_count()
        ram_gb = psutil.virtual_memory().total / (1024**3)

        if cpu_count <= 4 and ram_gb <= 8:
            self.low_end_hardware_radio.setChecked(True)
        elif cpu_count <= 8 and ram_gb <= 16:
            self.mid_range_hardware_radio.setChecked(True)
        else:
            self.high_end_hardware_radio.setChecked(True)

    def detect_server(self):
        import socket
        try:
            socket.create_connection(("localhost", 8000), timeout=1)
            self.local_server_radio.setChecked(True)
        except OSError:
            self.no_server_radio.setChecked(True)

    def create_shortcut(self):
        from pyshortcuts import make_shortcut
        make_shortcut("installer.py", name="Unified AI Project")

from PyQt5.QtWidgets import QLineEdit, QFormLayout

class APIKeyPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("API Keys")

        layout = QFormLayout()
        self.gemini_api_key_input = QLineEdit()
        self.openai_api_key_input = QLineEdit()
        layout.addRow("Gemini API Key:", self.gemini_api_key_input)
        layout.addRow("OpenAI API Key:", self.openai_api_key_input)
        self.setLayout(layout)

from PyQt5.QtWidgets import QPushButton

class FinishedPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Finished")
        layout = QVBoxLayout()
        self.finished_label = QLabel("The installation is complete.")
        layout.addWidget(self.finished_label)
        self.reconfigure_button = QPushButton("Reconfigure")
        self.reconfigure_button.clicked.connect(self.reconfigure)
        layout.addWidget(self.reconfigure_button)
        self.setLayout(layout)

    def initializePage(self):
        self.save_python_path()

    def save_python_path(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env_path = os.path.join(project_root, '.env')
        try:
            with open(env_path, 'a') as f:
                f.write(f"\nPYTHON_EXECUTABLE={sys.executable}\n")
            print(f"Python executable path saved to {env_path}")
            self.finished_label.setText("The installation is complete.\nPython path saved.")
        except Exception as e:
            print(f"Error saving Python executable path: {e}", file=sys.stderr)
            self.finished_label.setText(f"The installation is complete.\nCould not save Python path: {e}")

    def reconfigure(self):
        self.wizard().restart()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = InstallationWizard()
    wizard.show()
    sys.exit(app.exec_())
