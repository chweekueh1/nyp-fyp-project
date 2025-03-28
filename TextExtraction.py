from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from unstructured.partition.common import UnsupportedFileFormatError
from langchain_community.document_transformers.openai_functions import create_metadata_tagger
from langchain.schema import Document
from langchain_openai import ChatOpenAI
import openai
import os
import shutil
from glob import glob
from dotenv import load_dotenv
import magic
from keybert import KeyBERT
from keybert.llm import OpenAI
from keybert import KeyLLM
import zipfile
import mimetypes
import warnings

warnings.filterwarnings("ignore")

# load environment variables for secure configuration
load_dotenv()

CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
CLASSIFICATION_DATA_PATH = os.getenv("CLASSIFICATION_DATA_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai.api_key)

def main(file):

    # extract text from file
    try:
        document = ExtractText(file)
    except UnsupportedFileFormatError:
        directory = os.path.join(CHAT_DATA_PATH, 'error files')
        os.makedirs(directory, exist_ok=True)
        shutil.move(file, directory)

    # metadata keyword tagging for document
    document = OpenAIMetadataTagger(document)
    print(document[0].metadata)
    print('\n')

    document[0].metadata['keywords'] = KeyBERTMetadataTagger(document[0].page_content)
    print(document[0].metadata)
    print('\n')

    document[0].metadata['keywords'] = KeyBERTOpenAIMetadataTagger(document[0].page_content)
    print(document[0].metadata)
    print('\n')

    # semantic chunking

    # metadata keyword tagging for chunk

    # batching for efficient processing

    # create and populate the vector database with document embeddings
    

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


# function to load files using an extension of unstructured partition with langchain's document loaders
def ExtractText(path):
    loader = UnstructuredFileLoader(path, encoding='utf-8')
    documents = loader.load()
    return documents


# function to create metadata keyword tags for document and chunk using OpenAI
def OpenAIMetadataTagger(document):
    
    schema = { 
        "properties": {
            "keywords": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "The top 5–10 keywords that best represent the document's main topics or concepts.",
                "uniqueItems": True,
                "minItems": 10
            },
        },
        "required": ["keywords"]
    }

    llm = ChatOpenAI(temperature=0.8, model="gpt-4o")

    document_transformer = create_metadata_tagger(metadata_schema=schema, llm=llm)
    enhanced_documents = document_transformer.transform_documents(document)
    return enhanced_documents


# function to create metadata keyword tags for document and chunk using keyBERT library
def KeyBERTMetadataTagger(document):

    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(document, keyphrase_ngram_range=(1, 2), use_maxsum=True, nr_candidates=20, top_n=5, stop_words='english')
    return keywords


# function to create metadata keyword tags for document and chunk using keyBERT library extended with openAI through langchain
# This function outputs the same results as OpenAIMetadataTagger except it seems to have an issue of counting punctuation as a keyword
# This is likely due to the how the KeyLLM is implemented in the keyBERT library
# This function is kept here as an archive and for future reference but will not be used in the final implementation
def KeyBERTOpenAIMetadataTagger(document):

    # Create your LLM
    llm = OpenAI(client)
    kw_model = KeyLLM(llm)

    # Load it in KeyLLM
    kw_model = KeyLLM(llm)

    # Extract keywords
    keywords = kw_model.extract_keywords(document,check_vocab=True)

    return keywords


# function to split documents into smaller chunks for better processing
# includes overlap to maintain context between chunks
def chunking(document):
    pass


files = glob(CHAT_DATA_PATH + '/**/*.*', recursive=True)

main("modelling\\data\\pdf_files\\CyberSecurity - Home.pdf")