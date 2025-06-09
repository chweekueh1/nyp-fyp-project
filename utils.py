import os

def rel2abspath(relative_path: str) -> str:
    return os.path.abspath(relative_path)

def create_folders(path: str):
    if not path.endswith('\\'):
        folder_path = os.path.dirname(path)
    else:
        folder_path = path
    os.makedirs(folder_path, exist_ok=True)
