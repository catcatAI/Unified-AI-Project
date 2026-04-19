import subprocess
import json
import os

class OSBridgeAdapter:
    """
    Adapter to connect the Unified-AI-Project Backend with the Gemini OS Bridge.
    """
    def __init__(self):
        # Path to the bridge script relative to the root
        self.bridge_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../../../../gemini-os-bridge/bridge.py"
        ))
        self.python_exe = "python" # Or path to venv python

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
