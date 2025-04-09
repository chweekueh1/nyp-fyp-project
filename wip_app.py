import os
import zipfile
import mimetypes
import magic
from flask import Flask, request, jsonify


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

# Route for file uploads
@app.route('/upload', methods=['POST'])
def upload_file():


if __name__ == '__main__':
    os.makedirs('modelling\\data\\error_files', exist_ok=True)
    os.makedirs('modelling\\data\\temp', exist_ok=True)