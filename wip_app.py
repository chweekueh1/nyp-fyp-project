import os
import shutil
import zipfile
from dotenv import load_dotenv
import mimetypes
import magic
from fastapi import FastAPI, File, UploadFile
from unstructured.partition.common import UnsupportedFileFormatError
from TextExtraction import dataProcessing

load_dotenv()

CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
app = FastAPI()

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
@app.route('/upload')
async def upload(file: UploadFile = File(...)):
    try:
        
        contents = file.file.read()
        temp_directory = os.path.join(CHAT_DATA_PATH, 'temp')
        os.makedirs(temp_directory, exist_ok=True)
        file_path = os.path.join(temp_directory, file.filename)
        with open(file_path, 'wb') as f:
            f.write(contents)
            f.close()
        try:
            dataProcessing(file_path)
        except UnsupportedFileFormatError:        
            raise Exception(detail="Filetype not supported")
        
        file_type = detectFileType(file_path)
        directory = os.path.join(CHAT_DATA_PATH, f'{file_type[1:]}_files')
        os.makedirs(directory, exist_ok=True)
        shutil.move(file_path, directory)        

    except Exception as e:

        return {"success":False, "error":True, "message": f"File upload error: {str(e)}"}
        #raise HTTPException(status_code=500, error=True, detail=f'File upload error: {str(e)}')

if __name__ == '__main__':
    pass