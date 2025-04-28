import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import shutil
import logging
import time
import secrets
import string
import traceback
import zipfile
from dotenv import load_dotenv
import mimetypes
import magic
from unstructured.partition.common import UnsupportedFileFormatError
from langchain_chroma import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from dataProcessing import dataProcessing, initialiseDatabase

load_dotenv()

CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
DATABASE_PATH = os.getenv('DATABASE_PATH')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')

db = Chroma(
    collection_name = 'classification',
    embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    persist_directory=DATABASE_PATH
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = CHAT_DATA_PATH
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024

# function to detect file type using magic and mimetypes
def detectFileType(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    file_extension = mimetypes.guess_extension(mime_type)

    # fix for Office files detected as zip
    if file_extension == ".zip":
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                zip_contents = z.namelist()

                if any(f.startswith("ppt") for f in zip_contents):
                    file_extension = ".pptx" 
                elif any(f.startswith("word") for f in zip_contents):
                    file_extension = ".docx"  
                elif any(f.startswith("xl") for f in zip_contents):
                    file_extension = ".xlsx"

        except zipfile.BadZipFile:
            pass

    return file_extension

def generateUniqueFilename(filename, username, filetype):
    alphabet = string.ascii_letters + string.digits
    random_id = ''.join(secrets.choice(alphabet) for i in range(8))
    time_id = time.time_ns()
    final_filename = f'{filename}_{username}_{time_id}_{random_id}{filetype}'
    return final_filename

# Route for file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            logging.warning("No file part in the request.")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']

        if file.filename == '':
            logging.warning("Empty filename: %s", file.filename)
            return jsonify({'error': 'Invalid filename'}), 400
        
        contents = file.getvalue()
        filename = secure_filename(file.filename)
        temp_directory = os.path.join(CHAT_DATA_PATH, 'temp')
        os.makedirs(temp_directory, exist_ok=True)
        file_path = os.path.join(temp_directory, filename)
        with open(file_path, 'wb') as f:
            f.write(contents)
            f.close()

        try:
            dataProcessing(file_path)
        except UnsupportedFileFormatError:
            return jsonify({'error': 'Invalid file type'}), 400
        
        file_type = detectFileType(file_path)
        directory = os.path.join(CHAT_DATA_PATH, f'{file_type[1:]}_files')
        os.makedirs(directory, exist_ok=True)
        username = request.form.get('username')
        new_file_name = generateUniqueFilename(filename=filename, username=username, filetype=file_type)
        full_directory = os.path.join(directory, new_file_name)
        shutil.copy(file_path, full_directory)

        shutil.rmtree(temp_directory)

    except Exception as e:
        logging.error("Error in /upload endpoint: %s", traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    if len(db.get()['classification']) == 0:
        initialiseDatabase()