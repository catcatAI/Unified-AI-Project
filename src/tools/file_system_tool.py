import os

def list_files(path):
    """
    Lists the files in a directory.

    Args:
        path: The path to the directory.

    Returns:
        A list of files in the directory.
    """
    return os.listdir(path)

def read_file(path):
    """
    Reads the contents of a file.

    Args:
        path: The path to the file.

    Returns:
        The contents of the file.
    """
    with open(path, "r") as f:
        return f.read()

def write_file(path, contents):
    """
    Writes contents to a file.

    Args:
        path: The path to the file.
        contents: The contents to be written to the file.
    """
    with open(path, "w") as f:
        f.write(contents)
