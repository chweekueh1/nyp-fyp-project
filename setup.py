import os
from dotenv import load_dotenv
from utils import rel2abspath, ensure_chatbot_dir_exists
import zipfile
import subprocess
import sys

load_dotenv()
PATH = os.getenv('DEPENDENCIES_PATH', '')

def extractDependencies():
    with zipfile.ZipFile(rel2abspath('.\\dependencies.zip'), 'r') as zip_ref:
        zip_ref.extractall(rel2abspath('$HOME\\.nypai-chatbot\\dependencies\\'))

def applyPath():
    full_path = []
    paths = PATH.split(';')
    for path in paths:
        dependency = rel2abspath(path)
        full_path.append(dependency)
    additional_path = ';' + ';'.join(full_path)
    os.environ['PATH'] += additional_path

def main():
    ensure_chatbot_dir_exists()
    extractDependencies()

    applyPath()

    subprocess.run([sys.executable, "-m", "venv", '.venv'], check=True)

    pip_path = rel2abspath(".venv\\Scripts\\pip.exe")

    subprocess.run([pip_path, "install", "-r", "requirements.txt"])

if __name__ == '__main__':
    main()
