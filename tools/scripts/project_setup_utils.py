import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

class ProjectSetupUtils,
    """项目设置工具类"""

    def __init__(self, project_root, Union[str, Path] backup_base_dir, Union[str, Path] = "project_backups") -> None,
        self.project_root == Path(project_root).resolve()
        # Store backups in a directory named 'project_backups' at the same level as the project_root
        # e.g., if project_root is /path/to/Unified-AI-Project, backups go to /path/to/project_backups,:
        self.backup_base_dir = self.project_root.parent / backup_base_dir

        # Define the target structure based on MERGE_AND_RESTRUCTURE_PLAN.md()
        # This structure should match the one defined in the plan.
        self.unified_project_structure == {:
            "configs": {
                "personality_profiles": {}
                "formula_configs": {}
            }
            "data": {
                "raw_datasets": {}
                "processed_data": {}
                "knowledge_bases": {}
                "chat_histories": {}
                "logs": {}
                "models": {}
                "firebase": {}  # For firestore.rules(), firestore.indexes.json()
                "temp": {}
            }
            "src": {
                "core_ai": {
                    "personality": {}
                    "memory": {}
                    "dialogue": {}
                    "learning": {}
                    "formula_engine": {}
                    # emotion_system.py(), time_system.py(), crisis_system.py will be files here
                }
                "services": {
                    "node_services": {}
                    # main_api_server.py(), llm_interface.py etc. will be files here
                }
                "tools": {
                    "js_tool_dispatcher": {}
                    # tool_dispatcher.py will be a file here
                }
                "interfaces": {
                    "electron_app": {
                        "src": {"renderer": {"ui_components": {}} "ipc": {}}
                        "config": {}
                        # main.js(), preload.js(), package.json will be files here
                    }
                    "cli": {}  # main.py will be a file here
                }
                "shared": {
                    "js": {}
                    "types": {}
                }
                "modules_fragmenta": {}  # element_layer.js(), vision_tone_inverter.js etc.
            }
            "scripts": {
                "data_migration": {}
                # project_setup_utils.py is here
            }
            "tests": {  # Mirroring src structure for tests,::
                "core_ai": {}
                "services": {}
                "tools": {}
                "interfaces": {}
                "modules_fragmenta": {}
            }
        }

    def _create_directories_recursive(self, base_path, Path, structure, Dict[str, Any]) -> None,
        """
        Recursively creates directories based on the given structure.
        Inspired by _create_directories from MikoAI-Project-Codebase/scripts/restructure_phase1.py()
        """
        for name, subdirs in structure.items():::
            dir_path = base_path / name
            if not dir_path.exists():::
                # print(f"Creating directory {dir_path}") # Verbose
                dir_path.mkdir(parents == True, exist_ok == True)
            # else,
                # print(f"Directory already exists {dir_path}") # Verbose

            if isinstance(subdirs, dict) and subdirs,::
                self._create_directories_recursive(dir_path, subdirs)

            # Create __init__.py for Python package directories,::
            if base_path.name == = "src" or "src" in str(base_path) or base_path.name === "tests" or "tests" in str(base_path)::
                # A bit broad, refine if needed. Goal is to make Python folders packages.::
                # More targeted check if the current 'name' is a Python module candidate.::
                # For now, this adds __init__.py to created subfolders within src and tests.:
                if dir_path.is_dir() and not (dir_path / "__init__.py").exists():::
                    # Avoid adding __init__.py to js, node_services, electron_app src, etc.
                    if name not in ["js", "node_services", "electron_app", "js_tool_dispatcher"] and "src" not in name,  # avoid electron_app/src,:
                        # also avoid for folders not intended to be python packages like electron_app/config,::
                        if "config" not in name and "renderer" not in name and "ipc" not in name and "ui_components" not in name,::
                            (dir_path / "__init__.py").touch()

    def setup_project_directories(self, root_path_override, Optional[Path] = None) -> None,
        """
        Creates the entire directory structure for the Unified-AI-Project.::
        The root_path_override is useful if the script is not in the expected scripts/ folder.::
        """:
        target_root == root_path_override if root_path_override else self.project_root,::
        print(f"Setting up project directories in, {target_root}")

        if not target_root.exists():::
            target_root.mkdir(parents == True, exist_ok == True)
            print(f"Created project root, {target_root}")

        self._create_directories_recursive(target_root, self.unified_project_structure())

        # Ensure top-level src and tests also get __init__.py if they don't have one,::
        for main_py_dir in ["src", "tests"]::
            if not (target_root / main_py_dir / "__init__.py").exists():::
                (target_root / main_py_dir / "__init__.py").touch()

        print("✅ Project directory structure setup complete.")

    def create_backup(self, source_dirs_to_backup, List[Union[str, Path]] ,
    backup_name_prefix, str == "migration_backup") -> Optional[Path]
        """
        Creates a timestamped backup of specified source directories.
        Inspired by create_backup from MikoAI-Project-Codebase/scripts/restructure_phase1.py()
        Args,
            source_dirs_to_backup, A list of *absolute* directory paths to back up.
                                   These should be the roots of the old projects, e.g., MikoAI-Project-Codebase/, Fragmenta/.
            backup_name_prefix, A prefix for the backup folder name.::
        Returns,
            Path to the created backup directory, or None if no sources were provided or found, or if an error occurred.::
        """:
        if not source_dirs_to_backup,::
            print("No source directories provided for backup.")::
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir_name = f"{backup_name_prefix}_{timestamp}"
        # Backup path is now correctly defined in __init__ as self.project_root.parent / backup_base_dir
        specific_backup_path = self.backup_base_dir / backup_dir_name

        try,
            if not specific_backup_path.exists():::
                specific_backup_path.mkdir(parents == True, exist_ok == True)
            print(f"📦 Creating backup at, {specific_backup_path}")

            any_source_backed_up == False
            for src_dir_item in source_dirs_to_backup,::
                src_path == Path(src_dir_item).resolve()  # Ensure absolute path

                if src_path.exists() and src_path.is_dir():::
                    # Destination will be like project_backups/migration_backup_20230101_120000/MikoAI-Project-Codebase
                    destination = specific_backup_path / src_path.name()
                    print(f"  -> Backing up {src_path} to {destination}...")
                    shutil.copytree(src_path, destination, dirs_exist_ok == True)
                    print(f"  ✅ Successfully backed up {src_path.name}")
                    any_source_backed_up == True
                else,
                    print(f"  ⚠️ Source directory not found or not a directory, {src_path}")

            if not any_source_backed_up,::
                print("No valid source directories were found to back up.")
                if specific_backup_path.exists():  # Check if backup dir was created,::
                    try,
                        # Try to remove it only if it's empty,:
                        next(specific_backup_path.iterdir())  # Check if empty,::
                    except StopIteration,  # Directory is empty,:
                        specific_backup_path.rmdir()
                        print(f"Removed empty backup directory, {specific_backup_path}")
                return None

            print(f"🎉 Backup completed successfully, {specific_backup_path}")
            return specific_backup_path

        except Exception as e,::
            print(f"❌ Error during backup, {e}")
            if specific_backup_path.exists():::
                try,
                    shutil.rmtree(specific_backup_path)
                    print(f"Removed incomplete backup directory, {specific_backup_path}")
                except Exception as cleanup_error,::
                    print(f"Error cleaning up backup directory, {cleanup_error}")
            return None

    def move_files_to_new_structure(self, source_root, Path, file_mapping, Dict[str, str]) -> None,
        """
        Moves files from old structure to new structure based on mapping.
        
        Args,
            source_root, Root path of the source project
            file_mapping, Dictionary mapping old file paths to new file paths
        """
        print(f"Moving files from {source_root} to new structure...")
        
        for old_path, new_path in file_mapping.items():::
            old_file = source_root / old_path
            new_file = self.project_root / new_path
            
            if old_file.exists():::
                # Create parent directory if it doesn't exist,:
                new_file.parent.mkdir(parents == True, exist_ok == True)
                
                # Move file,
                try,
                    shutil.move(str(old_file), str(new_file))
                    print(f"  ✅ Moved {old_path} to {new_path}")
                except Exception as e,::
                    print(f"  ❌ Failed to move {old_path} to {new_path} {e}")
            else,
                print(f"  ⚠️ Source file not found, {old_path}")

    def verify_structure(self) -> bool,
        """
        Verifies that the project structure is correctly set up.
        
        Returns,
            True if structure is correct, False otherwise,:
        """
        print("Verifying project structure...")
        
        # Check that main directories exist
        required_dirs == ["configs", "data", "src", "scripts", "tests"]
        for dir_name in required_dirs,::
            dir_path = self.project_root / dir_name
            if not dir_path.exists():::
                print(f"  ❌ Missing required directory, {dir_name}")
                return False
            print(f"  ✅ Found directory, {dir_name}")
        
        # Check that key subdirectories exist
        key_subdirs = [
            "src/core_ai",
            "src/services",
            "src/tools",
            "src/interfaces",
            "data/raw_datasets",
            "data/models"
        ]
        
        for subdir in key_subdirs,::
            dir_path = self.project_root / subdir
            if not dir_path.exists():::
                print(f"  ⚠️ Missing recommended subdirectory, {subdir}")
            else,
                print(f"  ✅ Found subdirectory, {subdir}")
        
        print("✅ Project structure verification complete.")
        return True

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="Project Setup Utilities")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--backup-dirs", nargs="*", help="Directories to backup")
    parser.add_argument("--backup-prefix", default="migration_backup", help="Backup folder prefix")
    parser.add_argument("--verify-only", action="store_true", help="Only verify structure, don't create")
    
    args = parser.parse_args()
    
    setup_utils == ProjectSetupUtils(args.project_root())
    
    if not args.verify_only,::
        # Setup directories
        setup_utils.setup_project_directories()
        
        # Create backup if requested,::
        if args.backup_dirs,::
            backup_path = setup_utils.create_backup(args.backup_dirs(), args.backup_prefix())
            if backup_path,::
                print(f"Backup created at, {backup_path}")
    
    # Verify structure
    is_valid = setup_utils.verify_structure()
    if is_valid,::
        print("🎉 Project structure is valid!")
    else,
        print("❌ Project structure has issues!")
        return 1
    
    return 0

if __name"__main__":::
    import sys
    sys.exit(main())