# Placeholder for Crisis Management System
# This system will detect and manage crisis situations, potentially involving safety protocols,
# user well-being checks, or handing off to other support systems.
from datetime import datetime

class CrisisSystem:
    def __init__(self, config: dict = None, emotion_system_ref=None, memory_system_ref=None):
        self.config = config or {}
        self.emotion_system = emotion_system_ref # Reference to an EmotionSystem instance
        self.memory_system = memory_system_ref   # Reference to a MemoryManager instance
        self.crisis_level = 0 # 0 = No crisis, higher numbers indicate severity

        # Load configuration from file if not provided
        if not self.config:
            self._load_config_from_file()

        # Default crisis keywords if not provided in config
        self.crisis_keywords = self.config.get("crisis_keywords", [])
        self.default_crisis_level = self.config.get("default_crisis_level_on_keyword", 1)
        self.crisis_protocols = self.config.get("crisis_protocols", {})
        print(f"CrisisSystem initialized. Keywords: {self.crisis_keywords}")

    def assess_input_for_crisis(self, input_data: dict, context: dict = None) -> int:
        """
        Assesses input and context for potential crisis indicators.
        Updates self.crisis_level.
        Returns the current crisis level.
        """
        text_input = input_data.get("text", "").lower()

        # Simple sentiment analysis
        negative_words = ["sad", "angry", "hate", "kill", "depressed"]
        sentiment_score = sum([1 for word in negative_words if word in text_input.split()])

        detected_level = 0
        if sentiment_score > 0:
            detected_level = 1

        for keyword in self.crisis_keywords:
            if keyword in text_input:
                detected_level = self.default_crisis_level
                break

        if detected_level > 0:
            if detected_level > self.crisis_level:
                 print(f"CrisisSystem: Potential crisis detected or level escalated. New level: {detected_level}.")
            elif detected_level < self.crisis_level:
                 print(f"CrisisSystem: Input suggests potential de-escalation, but maintaining current crisis level {self.crisis_level} until resolved.")
                 # For now, crisis level only goes up through assess, and down through resolve_crisis.
                 # More sophisticated logic could allow assess_input to also de-escalate.
                 return self.crisis_level # Return current higher level
            else: # detected_level == self.crisis_level and self.crisis_level > 0
                print(f"CrisisSystem: Input is consistent with ongoing crisis level {self.crisis_level}.")

            self.crisis_level = detected_level # Set or maintain the detected crisis level
            self._trigger_protocol(self.crisis_level, {"input_text": text_input, "context": context})
        else: # No crisis keywords detected in this input
            if self.crisis_level > 0:
                print(f"CrisisSystem: No crisis keywords in current input, but maintaining ongoing crisis level {self.crisis_level} until explicitly resolved.")
            # If self.crisis_level was 0, it remains 0.

        return self.crisis_level

    def _trigger_protocol(self, level: int, details: dict):
        """
        Triggers a protocol based on the crisis level.
        Simulates basic actions for now.
        """
        protocol_key = str(level)
        action_details = self.crisis_protocols.get(protocol_key, self.crisis_protocols.get("default", "log_only"))

        print(f"CrisisSystem: Level {level} detected. Executing protocol: '{action_details}'. Input details: {details.get('input_text', 'N/A')[:50]}...")

        if action_details == "log_and_monitor_basic_crisis_response":
            with open("crisis_log.txt", "a") as f:
                f.write(f"[{datetime.now()}] CRISIS_LOG: Level {level} event. Details: {details}\n")
            print(f"CRISIS_LOG: Level {level} event. Details: {details}")
        elif action_details == "notify_human_moderator": # Example from previous version
            print(f"CRITICAL_ALERT: Human moderator notification required for crisis level {level}. Details: {details}")
        elif action_details == "log_only":
             print(f"CRISIS_INFO: Level {level} event logged. Details: {details}")
        else:
            print(f"CRISIS_INFO: Protocol '{action_details}' executed for level {level}.")

    def get_current_crisis_level(self) -> int:
        return self.crisis_level

    def resolve_crisis(self, resolution_details: str):
        """Manually or automatically resolves/de-escalates a crisis."""
        print(f"CrisisSystem: Crisis level {self.crisis_level} resolved. Details: {resolution_details}")
        self.crisis_level = 0

    def _load_config_from_file(self):
        """Loads configuration from a JSON file."""
        import json
        import os
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, '..', '..', 'configs', 'crisis_system_config.json')
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading crisis system config: {e}")
            self.config = {}


if __name__ == '__main__':
    example_config = {
        "crisis_keywords": ["emergency help", "i am scared"],
        "default_crisis_level_on_keyword": 2,
        "crisis_protocols": {
            "1": "monitor_closely",
            "2": "offer_support_resources",
            "3": "notify_human_moderator",
            "default": "log_and_monitor"
        }
    }
    crisis_sys = CrisisSystem(config=example_config)

    print(f"Initial crisis level: {crisis_sys.get_current_crisis_level()}")

    sample_input_normal = {"text": "Tell me a joke."}
    crisis_sys.assess_input_for_crisis(sample_input_normal)
    print(f"Crisis level after normal input: {crisis_sys.get_current_crisis_level()}")

    sample_input_crisis = {"text": "I need emergency help right now!"}
    crisis_sys.assess_input_for_crisis(sample_input_crisis)
    print(f"Crisis level after crisis input: {crisis_sys.get_current_crisis_level()}")

    crisis_sys.resolve_crisis("User confirmed they are okay, false alarm.")
    print(f"Crisis level after resolution: {crisis_sys.get_current_crisis_level()}")
