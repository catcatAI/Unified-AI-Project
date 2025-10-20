import sys
import yaml
import os
from PyQt5.QtWidgets import QApplication, QWizard, QWizardPage, QVBoxLayout, QLabel, QComboBox

class InstallationWizard(QWizard):
    def __init__(self) -> None:
        _ = super().__init__()

        self.translator = QTranslator()
        self.current_locale = QLocale.system().name()
        _ = self.load_translator(self.current_locale)

        # Load dependency configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'configs', 'dependency_config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.dependency_config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: dependency_config.yaml not found at {config_path}", file=sys.stderr)
            self.dependency_config = {} # Fallback to empty config
        except yaml.YAMLError as e:
            print(f"Error parsing dependency_config.yaml: {e}", file=sys.stderr)
            self.dependency_config = {} # Fallback to empty config

        _ = self.addPage(WelcomePage())
        _ = self.addPage(ConfigurationPage())
        _ = self.addPage(APIKeyPage())
        _ = self.addPage(InstallationPage())
        _ = self.addPage(FinishedPage())

        _ = self.setWindowTitle(self.tr("Installation Wizard"))
        self.selected_installation_type = None # Added to store the selected type

    def load_translator(self, locale):
        if self.translator.load(f"installer_{locale}", "."):
            _ = QApplication.instance().installTranslator(self.translator)
            print(f"Loaded translator for {locale}")
        else:
            print(f"Could not load translator for {locale}")

    def change_language(self, index):
        locale = self.sender().itemData(index)
        if locale != self.current_locale:
            _ = QApplication.instance().removeTranslator(self.translator)
            _ = self.load_translator(locale)
            self.current_locale = locale
            _ = self.retranslateUi()
            # Retranslate all pages
            for i in range(self.pageIds().count()):
                page = self.page(self.pageIds().at(i))
                if hasattr(page, 'retranslateUi'):
                    _ = page.retranslateUi()

    def retranslateUi(self):
        _ = self.setWindowTitle(self.tr("Installation Wizard"))
        for i in range(self.pageIds()):
            page = self.page(self.pageIds()[i])
            if hasattr(page, 'retranslateUi'):
                _ = page.retranslateUi()

    def get_os(self):
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("darwin"):
            return "macos"
        else:
            return "linux"

class WelcomePage(QWizardPage):
    def __init__(self) -> None:
        _ = super().__init__()
        _ = self.setTitle(self.tr("Welcome"))
        layout = QVBoxLayout()
        self.welcome_label = QLabel(self.tr("Welcome to the Unified AI Project installation wizard."))
        _ = layout.addWidget(self.welcome_label)

        # Language selection
        language_group = QGroupBox(self.tr("Language"))
        language_layout = QVBoxLayout()
        self.language_combo = QComboBox()
        _ = self.language_combo.addItem(self.tr("English"), "en_US")
        _ = self.language_combo.addItem(self.tr("Chinese (中文)"), "zh_CN")
        _ = self.language_combo.addItem(self.tr("Japanese (日本語)"), "ja_JP")
        _ = self.language_combo.currentIndexChanged.connect(self.wizard().change_language)
        _ = language_layout.addWidget(self.language_combo)
        _ = language_group.setLayout(language_layout)
        _ = layout.addWidget(language_group)

        _ = self.setLayout(layout)

    def retranslateUi(self):
        _ = self.setTitle(self.tr("Welcome"))
        _ = self.welcome_label.setText(self.tr("Welcome to the Unified AI Project installation wizard."))
        _ = self.findChild(QGroupBox, self.tr("Language")).setTitle(self.tr("Language"))
        # Update combo box items for language selection
        # This is a bit tricky as addItem doesn't directly support retranslation of existing items.
        # A simple approach is to clear and re-add, but that might reset selection.
        # For now, we'll rely on the wizard's retranslateUi to handle page titles and labels.
        # The language names in the combo box itself are handled by the initial setup and tr() calls.


from PyQt5.QtWidgets import QRadioButton, QGroupBox

class ConfigurationPage(QWizardPage):
    def __init__(self) -> None:
        _ = super().__init__()
        _ = self.setTitle(self.tr("Configuration"))

        layout = QVBoxLayout()

        # Installation Type configuration
        self.install_type_group = QGroupBox(self.tr("Installation Type"))
        install_type_layout = QVBoxLayout()
        self.install_type_combo = QComboBox()
        
        _ = install_type_layout.addWidget(QLabel(self.tr("Select the desired installation type:")))
        _ = install_type_layout.addWidget(self.install_type_combo)
        _ = self.install_type_group.setLayout(install_type_layout)
        _ = layout.addWidget(self.install_type_group)

        # Connect signal to update wizard's selected_installation_type
        _ = self.install_type_combo.currentIndexChanged.connect(self._update_selected_type)

        # Hardware configuration
        self.hardware_group = QGroupBox(self.tr("Hardware Configuration"))
        hardware_layout = QVBoxLayout()
        self.low_end_hardware_radio = QRadioButton(self.tr("Low-end hardware"))
        self.mid_range_hardware_radio = QRadioButton(self.tr("Mid-range hardware"))
        self.high_end_hardware_radio = QRadioButton(self.tr("High-end hardware"))
        _ = hardware_layout.addWidget(self.low_end_hardware_radio)
        _ = hardware_layout.addWidget(self.mid_range_hardware_radio)
        _ = hardware_layout.addWidget(self.high_end_hardware_radio)
        _ = self.hardware_group.setLayout(hardware_layout)
        _ = layout.addWidget(self.hardware_group)

        # Server configuration
        self.server_group = QGroupBox(self.tr("Server Configuration"))
        server_layout = QVBoxLayout()
        self.no_server_radio = QRadioButton(self.tr("No server"))
        self.local_server_radio = QRadioButton(self.tr("Local server"))
        self.remote_server_radio = QRadioButton(self.tr("Remote server"))
        _ = server_layout.addWidget(self.no_server_radio)
        _ = server_layout.addWidget(self.local_server_radio)
        _ = server_layout.addWidget(self.remote_server_radio)
        _ = self.server_group.setLayout(server_layout)
        _ = layout.addWidget(self.server_group)

        _ = self.setLayout(layout)

    def _update_selected_type(self):
        self.wizard().selected_installation_type = self.install_type_combo.currentData()

    def initializePage(self):
        # Populate combo box from dependency_config.yaml
        _ = self.install_type_combo.clear()
        installation_types = self.wizard().dependency_config.get('installation', {})
        for install_type, details in installation_types.items():
            _ = self.install_type_combo.addItem(f"{install_type} ({details.get('description', '')})", install_type)

        # Set default selection if not already set
        if not self.wizard().selected_installation_type and self.install_type_combo.count() > 0:
            _ = self.install_type_combo.setCurrentIndex(0)
            _ = self._update_selected_type()

    def retranslateUi(self):
        _ = self.setTitle(self.tr("Configuration"))
        _ = self.install_type_group.setTitle(self.tr("Installation Type"))
        _ = self.install_type_group.findChild(QLabel).setText(self.tr("Select the desired installation type:"))
        _ = self.hardware_group.setTitle(self.tr("Hardware Configuration"))
        _ = self.low_end_hardware_radio.setText(self.tr("Low-end hardware"))
        _ = self.mid_range_hardware_radio.setText(self.tr("Mid-range hardware"))
        _ = self.high_end_hardware_radio.setText(self.tr("High-end hardware"))
        _ = self.server_group.setTitle(self.tr("Server Configuration"))
        _ = self.no_server_radio.setText(self.tr("No server"))
        _ = self.local_server_radio.setText(self.tr("Local server"))
        _ = self.remote_server_radio.setText(self.tr("Remote server"))

class InstallationPage(QWizardPage):
    def __init__(self) -> None:
        _ = super().__init__()
        _ = self.setTitle(self.tr("Installation"))
        layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        _ = layout.addWidget(self.progress_bar)
        _ = self.setLayout(layout)

    def retranslateUi(self):
        _ = self.setTitle(self.tr("Installation"))

    def initializePage(self):
        _ = self.progress_bar.setValue(0)
        _ = self.wizard().nextButton.setEnabled(False)
        import threading
        thread = threading.Thread(target=self.install_dependencies)
        _ = thread.start()

    def install_dependencies(self):
        import subprocess

        def install(package):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], timeout=300)
            except subprocess.CalledProcessError as e:
                _ = print(f"Error installing {package}: {e}")
            except subprocess.TimeoutExpired as e:
                _ = print(f"Timeout installing {package}: {e}")

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
            _ = self.progress_bar.setValue(100)
            _ = self.wizard().nextButton.setEnabled(True)
            return

        for i, dependency in enumerate(dependencies_to_install):
            _ = install(dependency)
            _ = self.progress_bar.setValue(int((i + 1) / len(dependencies_to_install) * 100))

        _ = self.create_shortcut()
        _ = self.wizard().nextButton.setEnabled(True)

    def detect_hardware(self):
        import psutil

        cpu_count = psutil.cpu_count()
        ram_gb = psutil.virtual_memory().total / (1024**3)

        if cpu_count <= 4 and ram_gb <= 8:
            _ = self.low_end_hardware_radio.setChecked(True)
        elif cpu_count <= 8 and ram_gb <= 16:
            _ = self.mid_range_hardware_radio.setChecked(True)
        else:
            _ = self.high_end_hardware_radio.setChecked(True)

    def detect_server(self):
        import socket
        try:
            socket.create_connection(("localhost", 8000), timeout=1)
            _ = self.local_server_radio.setChecked(True)
        except OSError:
            _ = self.no_server_radio.setChecked(True)

    def create_shortcut(self):
        from pyshortcuts import make_shortcut
        make_shortcut("installer.py", name="Unified AI Project")

from PyQt5.QtWidgets import QLineEdit, QFormLayout

class APIKeyPage(QWizardPage):
    def __init__(self) -> None:
        _ = super().__init__()
        _ = self.setTitle(self.tr("API Keys"))

        layout = QFormLayout()
        self.gemini_api_key_input = QLineEdit()
        self.openai_api_key_input = QLineEdit()
        _ = layout.addRow(self.tr("Gemini API Key:"), self.gemini_api_key_input)
        _ = layout.addRow(self.tr("OpenAI API Key:"), self.openai_api_key_input)

    def retranslateUi(self):
        _ = self.setTitle(self.tr("API Keys"))
        # Re-add rows to update labels if necessary, or update existing labels
        # For simplicity, assuming labels are directly accessible or can be found
        # This part might need more robust implementation depending on QFormLayout's behavior
        # For now, just updating the title is sufficient for basic retranslation
        pass
        _ = self.setLayout(layout)

from PyQt5.QtWidgets import QPushButton

class FinishedPage(QWizardPage):
    def __init__(self) -> None:
        _ = super().__init__()
        _ = self.setTitle("Finished")
        layout = QVBoxLayout()
        self.finished_label = QLabel("The installation is complete.")
        _ = layout.addWidget(self.finished_label)
        self.reconfigure_button = QPushButton("Reconfigure")
        _ = self.reconfigure_button.clicked.connect(self.reconfigure)
        _ = layout.addWidget(self.reconfigure_button)
        _ = self.setLayout(layout)

    def initializePage(self):
        _ = self.save_python_path()

    def save_python_path(self):
        project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env_path = os.path.join(project_root, '.env')
        try:
            with open(env_path, 'a') as f:
                f.write(f"\nPYTHON_EXECUTABLE={sys.executable}\n")
            _ = print(f"Python executable path saved to {env_path}")
            _ = self.finished_label.setText("The installation is complete.\nPython path saved.")
        except Exception as e:
            print(f"Error saving Python executable path: {e}", file=sys.stderr)
            _ = self.finished_label.setText(f"The installation is complete.\nCould not save Python path: {e}")

    def reconfigure(self):
        _ = self.wizard().restart()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = InstallationWizard()
    _ = wizard.show()
    _ = sys.exit(app.exec_())