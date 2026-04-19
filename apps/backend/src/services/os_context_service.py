from ..integrations.os_bridge_adapter import OSBridgeAdapter

class OSContextService:
    def __init__(self):
        self.adapter = OSBridgeAdapter()

    def get_current_state_for_ai(self):
        """
        Gathers a clean summary of the OS state for the AI to understand user context.
        """
        summary = self.adapter.get_summary()
        if summary.get("status") == "success":
            return {
                "active_windows": summary.get("window_preview", []),
                "clipboard_snippet": summary.get("clipboard_preview", ""),
                "total_windows": summary.get("active_windows_count", 0)
            }
        return {"error": "OS Bridge unreachable"}

    def perform_intelligent_action(self, intent_description, target_text=None):
        """
        Maps a high-level AI intent to an OS action.
        """
        if "click" in intent_description and target_text:
            return self.adapter.take_action("click_text", [target_text])
        # Add more intent mappings here
        return {"status": "unsupported_intent"}

if __name__ == "__main__":
    service = OSContextService()
    print(service.get_current_state_for_ai())
