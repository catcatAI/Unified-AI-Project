# Placeholder for Personality Manager
# This module will be responsible for loading, managing, and applying personality profiles.
# It will interact with the emotion system and influence dialogue generation.

import json
import os
from pathlib import Path

class PersonalityManager:
    def __init__(self, personality_profiles_dir: str = None, default_profile_name: str = "miko_base"):
        if personality_profiles_dir:
            self.profiles_dir = Path(personality_profiles_dir)
        else:
            # Default path: Unified-AI-Project/configs/personality_profiles/
            current_script_path = Path(__file__).resolve() # src/core_ai/personality/personality_manager.py
            project_root = current_script_path.parent.parent.parent.parent # Unified-AI-Project/
            self.profiles_dir = project_root / "configs" / "personality_profiles"

        self.default_profile_name = default_profile_name
        self.current_personality = None
        self.available_profiles = self._scan_profiles()

        if not self.available_profiles:
            print(f"PersonalityManager: Warning - No personality profiles found in {self.profiles_dir}")

        self.load_personality(self.default_profile_name)
        print(f"PersonalityManager initialized. Profiles dir: {self.profiles_dir}")

    def _scan_profiles(self) -> dict:
        """Scans the profiles directory for available JSON personality files."""
        profiles = {}
        if not self.profiles_dir.exists() or not self.profiles_dir.is_dir():
            return profiles

        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile_name = data.get("profile_name")
                    if profile_name:
                        profiles[profile_name] = {"path": str(file_path), "display_name": data.get("display_name", profile_name)}
            except Exception as e:
                print(f"PersonalityManager: Error loading profile {file_path.name}: {e}")
        return profiles

    def load_personality(self, profile_name: str) -> bool:
        """Loads a specified personality profile."""
        if profile_name not in self.available_profiles:
            print(f"PersonalityManager: Profile '{profile_name}' not found. Trying default.")
            if self.default_profile_name in self.available_profiles:
                profile_name = self.default_profile_name
            else: # If default also not found
                print(f"PersonalityManager: Default profile '{self.default_profile_name}' also not found. No personality loaded.")
                self.current_personality = None
                return False

        profile_info = self.available_profiles[profile_name]
        try:
            with open(profile_info["path"], 'r', encoding='utf-8') as f:
                self.current_personality = json.load(f)
            print(f"PersonalityManager: Successfully loaded personality '{profile_name}'.")
            return True
        except Exception as e:
            print(f"PersonalityManager: Error loading profile '{profile_name}' from {profile_info['path']}: {e}")
            self.current_personality = None
            return False

    def get_current_personality_trait(self, trait_name: str, default_value=None):
        """Gets a specific trait from the current personality."""
        if not self.current_personality:
            return default_value
        # Example: access nested traits like communication_style.default_tone
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

    def list_available_profiles(self) -> list:
        return [
            {"name": name, "display_name": info.get("display_name", name)}
            for name, info in self.available_profiles.items()
        ]

if __name__ == '__main__':
    pm = PersonalityManager()

    print(f"\nAvailable profiles: {pm.list_available_profiles()}")

    if pm.current_personality:
        print(f"\nLoaded personality: {pm.current_personality.get('profile_name')}")
        print(f"Initial prompt: {pm.get_initial_prompt()}")
        print(f"Default tone: {pm.get_current_personality_trait('communication_style.tone_presets.default', 'neutral')}")
        print(f"A non-existent trait: {pm.get_current_personality_trait('fictional.trait', 'not set')}")
    else:
        print("\nNo personality loaded for testing.")

    # Test loading another profile if available (e.g., if a "formal_miko.json" existed)
    # pm.load_personality("formal_miko")
    # if pm.current_personality and pm.current_personality.get("profile_name") == "formal_miko":
    #     print(f"\nSwitched to formal_miko: {pm.get_initial_prompt()}")
    # else:
    #     print("\nCould not switch to 'formal_miko' (likely not found).")

    # Test loading a non-existent profile
    print("\n--- Test loading non-existent profile ---")
    success = pm.load_personality("non_existent_profile_abc123")
    print(f"Loading non_existent_profile_abc123 success: {success}")
    if pm.current_personality:
         print(f"Current profile after trying to load non-existent: {pm.current_personality.get('profile_name')}")

    # Ensure it falls back to default if current was None or failed to load
    if not pm.current_personality and pm.default_profile_name in pm.available_profiles:
        pm.load_personality(pm.default_profile_name) # Explicitly reload default if needed
        print(f"Reverted to default profile: {pm.current_personality.get('profile_name')}")
