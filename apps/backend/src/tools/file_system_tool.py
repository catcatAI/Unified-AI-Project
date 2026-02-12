"""
File system operations tool
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def list_files(path: str) -> List[str]:
    """
    Lists the files in a directory.

    Args:
        path: The path to the directory.

    Returns:
        A list of files in the directory.
    """
    try:
        return os.listdir(path)
    except Exception as e:
        logger.error(f"Failed to list files in {path}: {e}")
        return []


def read_file(path: str) -> str:
    """
    Reads the contents of a file.

    Args:
        path: The path to the file.

    Returns:
        The contents of the file.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {path}: {e}")
        raise


def write_file(path: str, contents: str) -> bool:
    """
    Writes contents to a file.

    Args:
        path: The path to the file.
        contents: The contents to be written to the file.
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(contents)
        return True
    except Exception as e:
        logger.error(f"Failed to write file {path}: {e}")
        return False


class FileSystemTool:
    """File system operations tool for agents"""
    
    def __init__(self):
        self.name = "file_system"
        self.description = "Performs file system operations"
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute file system operation"""
        try:
            if action == "list":
                path = kwargs.get("path", ".")
                files = list_files(path)
                return {"success": True, "files": files}
            elif action == "read":
                path = kwargs.get("path")
                if not path:
                    return {"success": False, "error": "Path required"}
                content = read_file(path)
                return {"success": True, "content": content}
            elif action == "write":
                path = kwargs.get("path")
                content = kwargs.get("content", "")
                if not path:
                    return {"success": False, "error": "Path required"}
                success = write_file(path, content)
                return {"success": success}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return {"success": False, "error": str(e)}

