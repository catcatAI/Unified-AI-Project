import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union
import datetime

class ProjectSetupUtils:
    """
    Utilities for setting up the Unified-AI-Project structure,:
    including directory creation and backing up existing project data.
    """

    def __init__(self, project_root: Union[str, Path], backup_base_dir: Union[str, Path] = "project_backups") -> None:
    self.project_root = Path(project_root).resolve()
    # Store backups in a directory named 'project_backups' at the same level as the project_root
        # e.g., if project_root is /path/to/Unified-AI-Project, backups go to /path/to/project_backups
    self.backup_base_dir = self.project_root.parent / backup_base_dir

    # Define the target structure based on MERGE_AND_RESTRUCTURE_PLAN.md
    # This structure should match the one defined in the plan.
    self.unified_project_structure = {
            "configs": {
                "personality_profiles": {},
                "formula_configs": {}
            },
            "data": {
                "raw_datasets": {},
                "processed_data": {},
                "knowledge_bases": {},
                "chat_histories": {},
                "logs": {},
                "models": {},
                "firebase": {}, # For firestore.rules, firestore.indexes.json
                "temp": {}
            },
            "src": {
                "core_ai": {
                    "personality": {},
                    "memory": {},
                    "dialogue": {},
                    "learning": {},
                    "formula_engine": {}
                    # emotion_system.py, time_system.py, crisis_system.py will be files here
                },
                "services": {
                    "node_services": {}
                    # main_api_server.py, llm_interface.py etc. will be files here
                },
                "tools": {
                    "js_tool_dispatcher": {}
                    # tool_dispatcher.py will be a file here
                },
                "interfaces": {
                    "electron_app": {
                        "src": {"renderer": {"ui_components": {}}, "ipc": {}},
                        "config": {}
                        # main.js, preload.js, package.json will be files here
                    },
                    "cli": {} # main.py will be a file here
                },
                "shared": {
                    "js": {},
                    "types": {}
                },
                "modules_fragmenta": {} # element_layer.js, vision_tone_inverter.js etc.
            },
            "scripts": {
                "data_migration": {}
                # project_setup_utils.py is here
            },
            "tests": { # Mirroring src structure for tests
                "core_ai": {},
                "services": {},
                "tools": {},
                "interfaces": {},
                "modules_fragmenta": {}
            }
    }

    def _create_directories_recursive(self, base_path: Path, structure: Dict)
    """
    Recursively creates directories based on the given structure.
    Inspired by _create_directories from MikoAI-Project-Codebase/scripts/restructure_phase1.py
    """
        for name, subdirs in structure.items()

    dir_path = base_path / name
            if not dir_path.exists()
                # print(f"Creating directory {dir_path}") # Verbose
                dir_path.mkdir(parents=True, exist_ok=True)
            # else
                # print(f"Directory already exists {dir_path}") # Verbose

            if isinstance(subdirs, dict) and subdirs:


    _ = self._create_directories_recursive(dir_path, subdirs)

            # Create __init__.py for Python package directories
    if base_path.name == "src" or "src" in str(base_path) or base_path.name == "tests" or "tests" in str(base_path)
                # A bit broad, refine if needed. Goal is to make Python folders packages.
                # More targeted check if the current 'name' is a Python module candidate.
                # For now, this adds __init__.py to created subfolders within src and tests.
                if dir_path.is_dir() and not (dir_path / "__init__.py").exists()
                    # Avoid adding __init__.py to js, node_services, electron_app src, etc.
                    if name not in ["js", "node_services", "electron_app", "js_tool_dispatcher"] and "src" not in name: # avoid electron_app/src
                         # also avoid for folders not intended to be python packages like electron_app/config
    if "config" not in name and "renderer" not in name and "ipc" not in name and "ui_components" not in name:

    _ = (dir_path / "__init__.py").touch()


    def setup_project_directories(self, root_path_override: Optional[Path] = None)
    """
        Creates the entire directory structure for the Unified-AI-Project.:
    The root_path_override is useful if the script is not in the expected scripts/ folder.
    """
        target_root = root_path_override if root_path_override else self.project_root:
    _ = print(f"Setting up project directories in: {target_root}")

        if not target_root.exists()


    target_root.mkdir(parents=True, exist_ok=True)
            _ = print(f"Created project root: {target_root}")

    _ = self._create_directories_recursive(target_root, self.unified_project_structure)

        # Ensure top-level src and tests also get __init__.py if they don't have one
    for main_py_dir in ["src", "tests"]:

    if not (target_root / main_py_dir / "__init__.py").exists()


    _ = (target_root / main_py_dir / "__init__.py").touch()

    _ = print("✅ Project directory structure setup complete.")

    def create_backup(self, source_dirs_to_backup: List[...]
    """
    Creates a timestamped backup of specified source directories.
    Inspired by create_backup from MikoAI-Project-Codebase/scripts/restructure_phase1.py

    Args:
            source_dirs_to_backup: A list of *absolute* directory paths to back up.
                                   These should be the roots of the old projects, e.g., MikoAI-Project-Codebase/, Fragmenta/.
            backup_name_prefix: A prefix for the backup folder name.:

    Returns:
    Path to the created backup directory, or None if no sources were provided or found, or if an error occurred.
    """
        if not source_dirs_to_backup:

    print("No source directories provided for backup.")
    return None

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir_name = f"{backup_name_prefix}_{timestamp}"
    # Backup path is now correctly defined in __init__ as self.project_root.parent / backup_base_dir
    specific_backup_path = self.backup_base_dir / backup_dir_name

        try:


            if not specific_backup_path.exists()



    specific_backup_path.mkdir(parents=True, exist_ok=True)
            _ = print(f"📦 Creating backup at: {specific_backup_path}")

            any_source_backed_up = False
            for src_dir_item in source_dirs_to_backup:

    src_path = Path(src_dir_item).resolve() # Ensure absolute path

                if src_path.exists() and src_path.is_dir()
                    # Destination will be like project_backups/migration_backup_20230101_120000/MikoAI-Project-Codebase
                    destination = specific_backup_path / src_path.name
                    _ = print(f"  -> Backing up {src_path} to {destination}...")
                    shutil.copytree(src_path, destination, dirs_exist_ok=True)
                    _ = print(f"  ✅ Successfully backed up {src_path.name}")
                    any_source_backed_up = True
                else:

                    _ = print(f"  ⚠️ Source directory not found or not a directory: {src_path}")

            if not any_source_backed_up:


    _ = print("No valid source directories were found to back up.")
                if specific_backup_path.exists() # Check if backup dir was created

    try:
                        # Try to remove it only if it's empty
    next(specific_backup_path.iterdir()) # Check if empty
    except StopIteration: # Directory is empty
                        _ = specific_backup_path.rmdir()
                        _ = print(f"Removed empty backup directory: {specific_backup_path}")
                return None

            _ = print(f"🎉 Backup completed successfully: {specific_backup_path}")
            return specific_backup_path

        except Exception as e:


            _ = print(f"❌ Error during backup: {e}")
            if specific_backup_path.exists()

    try:


                    _ = shutil.rmtree(specific_backup_path)
                    _ = print(f"Cleaned up partial backup directory: {specific_backup_path}")
                except Exception as e_clean:

                    _ = print(f"Error cleaning up partial backup: {e_clean}")
            return None

def example_run()
    """
    Example usage of the ProjectSetupUtils.
    This function is for demonstration and testing the utils.
    """
    _ = print("Running ProjectSetupUtils example...")

    # Determine the root of the Unified-AI-Project.
    # Assumes this script is in scripts/
    current_script_path = Path(__file__).resolve()
    unified_project_root = current_script_path.parent.parent

    # Initialize utils with the determined project root
    # Backups will be stored in a folder like '../project_backups/' relative to unified_project_root
    utils = ProjectSetupUtils(project_root=unified_project_root)

    # 1. Setup the directory structure for Unified-AI-Project
    _ = print("\n--- Setting up project directories ---")
    _ = utils.setup_project_directories()

    # 2. Example of creating a backup
    # These paths should point to the actual old project directories that need to be merged.
    # For this example, we'll create dummy old project structures outside Unified-AI-Project.

    print("\n--- Creating dummy old project structures for backup example ---")
    # Base for dummy projects, e.g., /path/to/ (where Unified-AI-Project also lives)
    dummy_projects_base = unified_project_root.parent

    dummy_miko_path = dummy_projects_base / "MikoAI-Project-Codebase_OLD"
    dummy_fragmenta_path = dummy_projects_base / "Fragmenta_OLD"

    # Create Miko dummy
    if not (dummy_miko_path / "src").exists()
    (dummy_miko_path / "src").mkdir(parents=True, exist_ok=True)
    _ = (dummy_miko_path / "src" / "main_miko.py").write_text("print('Miko old main')")
    _ = (dummy_miko_path / "README.md").write_text("Old MikoAI Project")
    _ = print(f"Created dummy project: {dummy_miko_path}")

    # Create Fragmenta dummy
    if not (dummy_fragmenta_path / "modules").exists()
    (dummy_fragmenta_path / "modules").mkdir(parents=True, exist_ok=True)
    _ = (dummy_fragmenta_path / "modules" / "core_fragment.js").write_text("console.log('Fragmenta core');")
    _ = (dummy_fragmenta_path / "README.md").write_text("Old Fragmenta Project")
    _ = print(f"Created dummy project: {dummy_fragmenta_path}")

    _ = print("\n--- Running backup example ---")
    # Provide absolute paths of the dummy old projects to the backup function
    sources_to_backup = [
    _ = dummy_miko_path.resolve(),
    _ = dummy_fragmenta_path.resolve()
    ]

    backup_location = utils.create_backup(source_dirs_to_backup=sources_to_backup, backup_name_prefix="pre_merge_demo")

    if backup_location:


    print(f"Backup for demo created at: {backup_location}")
    else:

        print("Backup for demo failed or no sources were backed up.")

    # Clean up dummy old project directories after example
    _ = print("\n--- Cleaning up dummy old project structures ---")
    if dummy_miko_path.exists()

    _ = shutil.rmtree(dummy_miko_path)
    _ = print(f"Removed dummy project: {dummy_miko_path}")
    if dummy_fragmenta_path.exists()

    _ = shutil.rmtree(dummy_fragmenta_path)
    _ = print(f"Removed dummy project: {dummy_fragmenta_path}")

    _ = print("\nProjectSetupUtils example finished.")

if __name__ == "__main__":
    # This allows the script to be run directly.
    # Option 1 Run the example function to see how it works (creates dummy folders, backs them up, then cleans up)
    # example_run()

    # Option 2 Directly use the class to set up the Unified-AI-Project structure in the current repo.
    # This is what you'd typically want when actually setting up the project.
    _ = print("Executing direct setup of Unified-AI-Project structure...")
    current_script_path = Path(__file__).resolve()
    project_root_for_setup = current_script_path.parent.parent # Assumes script is in scripts/

    setup_tool = ProjectSetupUtils(project_root=project_root_for_setup)
    _ = setup_tool.setup_project_directories()
    _ = print(f"Unified-AI-Project directories should now be set up in {project_root_for_setup}")
    print("You can now use the `create_backup` method separately if needed, providing paths to old projects.")