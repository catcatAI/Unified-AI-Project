import subprocess
import json
import os
import sys
import asyncio
import logging

logger = logging.getLogger(__name__)

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

    async def _execute_async(self, command, *args):
        cmd = [self.python_exe, self.bridge_path, command] + list(args)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout:
                return json.loads(stdout.decode('utf-8'))
            return {"status": "error", "message": stderr.decode('utf-8')}
        except Exception as e:
            logger.warning(f"_execute_async failed for {command}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def _execute(self, command, *args):
        """Legacy synchronous execute - use _execute_async whenever possible"""
        cmd = [self.python_exe, self.bridge_path, command] + list(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if result.stdout:
                return json.loads(result.stdout)
            return {"status": "error", "message": result.stderr}
        except Exception as e:
            logger.warning(f"_execute failed for {command}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def get_summary(self) -> str:
        """Get the summary by self."""
        return await self._execute_async("summary")

    async def take_action(self, action_name, args=None) -> str:
        """Execute the take action operation."""
        task = [{"name": action_name, "args": args or []}]
        return await self._execute_async("task", json.dumps(task))

    async def get_screen_text(self) -> str:
        """Get the screen text by self."""
        return await self._execute_async("ocr")

if __name__ == "__main__":
    adapter = OSBridgeAdapter()
    print("Testing OS Bridge Adapter...")
    print(adapter.get_summary())
