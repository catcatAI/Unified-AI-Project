import subprocess
import json
import os
import sys

class OSBridgeAdapter:
    """
    Adapter to connect the Unified-AI-Project Backend with the Gemini OS Bridge.
    """
    def __init__(self):
        # Correct path: integrations -> src -> backend -> apps -> project_root
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_file_dir, "../../../../"))
        # The bridge is in Unified-AI-Project/apps/gemini-os-bridge/
        self.bridge_path = os.path.join(project_root, "apps", "gemini-os-bridge", "bridge.py")
        self.python_exe = sys.executable if "sys" in globals() else "python"
        
        # Verify path immediately on init for stability
        if not os.path.exists(self.bridge_path):
            # Fallback for different working directories
            alt_root = os.path.abspath(os.path.join(os.getcwd(), "apps/gemini-os-bridge/bridge.py"))
            if os.path.exists(alt_root):
                self.bridge_path = alt_root

    def _execute(self, command, *args):
        cmd = [self.python_exe, self.bridge_path, command] + list(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.stdout:
                return json.loads(result.stdout)
            return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_summary(self):
        return self._execute("summary")

    def take_action(self, action_name, args=None):
        task = [{"name": action_name, "args": args or []}]
        return self._execute("task", json.dumps(task))

    def get_screen_text(self):
        return self._execute("ocr")

if __name__ == "__main__":
    adapter = OSBridgeAdapter()
    print("Testing OS Bridge Adapter...")
    print(adapter.get_summary())
