# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L1+
# =============================================================================
#
# 职责: 文件系统工具，提供基本的文件操作
# 维度: 涉及所有维度
# 安全: 使用 Key A (后端控制)
# 成熟度: L1+ 等级
#
# =============================================================================

import os

def list_files(path: str) -> list:
    """
    Lists the files in a directory.

    Args:
        path: The path to the directory.

    Returns:
        A list of files in the directory.
    """
    return os.listdir(path)

def read_file(path: str) -> str:
    """
    Reads the contents of a file.

    Args:
        path: The path to the file.

    Returns:
        The contents of the file.
    """
    with open(path, "r", encoding='utf-8') as f:
        return f.read()

def write_file(path: str, contents: str):
    """
    Writes contents to a file.

    Args:
        path: The path to the file.
        contents: The contents to write.
    """
    with open(path, "w", encoding='utf-8') as f:
        f.write(contents)

def delete_file(path: str):
    """
    Deletes a file.

    Args:
        path: The path to the file.
    """
    os.remove(path)

def create_directory(path: str):
    """
    Creates a directory.

    Args:
        path: The path to the directory.
    """
    os.makedirs(path, exist_ok=True)

def file_exists(path: str) -> bool:
    """
    Checks if a file exists.

    Args:
        path: The path to the file.

    Returns:
        True if the file exists, False otherwise.
    """
    return os.path.exists(path)

def get_file_size(path: str) -> int:
    """
    Gets the size of a file.

    Args:
        path: The path to the file.

    Returns:
        The size of the file in bytes.
    """
    return os.path.getsize(path)