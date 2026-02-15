"""
Personality Manager
Handles loading and managing different personality profiles for the AI.
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class PersonalityManager:
    """
    Manages loading and managing different personality profiles for the AI.
    """

    def __init__(self, profiles_dir: Optional[Path] = None, default_profile_name: str = "default"):
        """
        Args:
            profiles_dir (Path, optional): Directory containing personality profile JSON files.
            default_profile_name (str): Name of the default personality profile to load.
        """
        self.profiles_dir = profiles_dir or Path(__file__).parent / "personalities"
        self.default_profile_name = default_profile_name
        self.available_profiles = self._scan_profiles()
        self.current_personality: Optional[Dict[str, Any]] = None
        
        # Try to load the default personality
        self.load_personality(self.default_profile_name)

    def _scan_profiles(self) -> Dict[str, Dict[str, str]]:
        """Scans the profiles directory for available JSON personality files."""
        profiles: Dict[str, Dict[str, str]] = {}
        if not self.profiles_dir.exists():
            logger.warning(f"PersonalityManager: Profiles directory {self.profiles_dir} does not exist.")
            return profiles

        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile_name = data.get("profile_name")
                    if profile_name:
                        profiles[profile_name] = {
                            "path": str(file_path),
                            "display_name": data.get("display_name", profile_name)
                        }
            except Exception as e:
                logger.error(f"PersonalityManager: Error loading profile {file_path.name}: {e}")
        return profiles

    def load_personality(self, profile_name: str) -> bool:
        """Loads a specified personality profile."""
        if profile_name not in self.available_profiles:
            logger.warning(f"PersonalityManager: Profile '{profile_name}' not found. Trying default.")
            if self.default_profile_name in self.available_profiles:
                profile_name = self.default_profile_name
            else:
                logger.error(f"PersonalityManager: Default profile '{self.default_profile_name}' also not found.")
                self.current_personality = None
                return False

        profile_info = self.available_profiles[profile_name]
        try:
            with open(profile_info["path"], 'r', encoding='utf-8') as f:
                self.current_personality = json.load(f)
            logger.info(f"PersonalityManager: Successfully loaded personality '{profile_name}'.")
            return True
        except Exception as e:
            logger.error(f"PersonalityManager: Error loading profile '{profile_name}' from {profile_info['path']}: {e}")
            self.current_personality = None
            return False

    def get_current_personality_trait(self, trait_name: str, default_value: Any = None) -> Any:
        """Gets a specific trait from the current personality."""
        if not self.current_personality:
            return default_value
            
        keys = trait_name.split('.')
        value = self.current_personality
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default_value

    def get_initial_prompt(self) -> str:
        """Returns the initial prompt for the current personality."""
        return self.get_current_personality_trait("initial_prompt", "Hello!")

    def list_available_profiles(self) -> List[Dict[str, str]]:
        """Lists all available personality profiles."""
        return [
            {"name": name, "display_name": info.get("display_name", name)}
            for name, info in self.available_profiles.items()
        ]

    def apply_personality_adjustment(self, adjustment: Dict[str, Any]):
        """
        Applies a personality adjustment to the current personality.
        """
        if not self.current_personality:
            return

        for key, value in adjustment.items():
            keys = key.split('.')
            target = self.current_personality
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            logger.info(f"PersonalityManager: Adjusted trait '{key}' to {value}.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pm = PersonalityManager()
    logger.info(f"Available profiles: {pm.list_available_profiles()}")