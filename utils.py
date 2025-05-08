import pathlib
import os

def rel2abspath(relative_path: str) -> str:
    return str((pathlib.Path().resolve() / relative_path).resolve())

def create_folders(path: str):
    if not path.endswith('\\'):
        folder_path = os.path.dirname(path)
    else:
        folder_path = path
    os.makedirs(folder_path, exist_ok=True)
