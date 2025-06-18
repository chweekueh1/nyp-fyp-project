from langchain_community.document_loaders.unstructured import UnstructuredFileLoader
from langchain_community.document_transformers.openai_functions import create_metadata_tagger
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
import openai
import os
from glob import glob
from dotenv import load_dotenv
from keybert import KeyBERT
from keybert.llm import OpenAI
from keybert import KeyLLM
import warnings
import shelve
from utils import create_folders, get_chatbot_dir, rel2abspath
import logging

warnings.filterwarnings("ignore")

# load environment variables for secure configuration
load_dotenv()

# Get paths and validate them
CHAT_DATA_PATH = os.path.join(get_chatbot_dir(), os.getenv("CHAT_DATA_PATH", ''))
CLASSIFICATION_DATA_PATH = rel2abspath(os.path.join(get_chatbot_dir(), os.getenv("CLASSIFICATION_DATA_PATH", '')))
KEYWORDS_DATABANK_PATH = rel2abspath((os.path.join(get_chatbot_dir(), os.getenv("KEYWORDS_DATABANK_PATH", ''))))
DATABASE_PATH = rel2abspath(os.path.join(get_chatbot_dir(), os.getenv('DATABASE_PATH', '')))
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')  # Default to a known model

# Validate OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.critical("OPENAI_API_KEY environment variable not set. LLM features will not work.")
    raise ValueError("OPENAI_API_KEY environment variable not set")

openai.api_key = OPENAI_API_KEY

# Create necessary folders
create_folders(KEYWORDS_DATABANK_PATH)

# Initialize databases with proper error handling
try:
    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    classification_db = Chroma(
        collection_name='classification',
        embedding_function=embedding,
        persist_directory=DATABASE_PATH
    )
    
    chat_db = Chroma(
        collection_name='chat',
        embedding_function=embedding,
        persist_directory=DATABASE_PATH
    )
    
    logging.info("Successfully initialized Chroma databases")
except Exception as e:
    logging.critical(f"Failed to initialize Chroma databases: {e}")
    raise

def dataProcessing(file, collection=chat_db):
    keywords_bank = []

    # extract text from file
    document = ExtractText(file)
    
    # metadata keyword tagging for document
    document = OpenAIMetadataTagger(document)
    
    for doc in document:
        if "keywords" in doc.metadata:
            keywords_bank.extend(doc.metadata['keywords'])
            for i in range(len(doc.metadata['keywords'])):
                doc.metadata[f'keyword{i}'] = doc.metadata['keywords'][i]
            doc.metadata["keywords"] = ", ".join(doc.metadata["keywords"])

    # chunking
    chunks = semanticChunker(list(document))

    # batching for efficient processing
    batches = batching(chunks,166)

    # create and populate the vector database with document embeddings
    databaseInsertion(batches=batches, collection=collection)

    # Update keywords databank with atomic file operations
    try:
        # Create a temporary file for atomic write
        temp_db_path = f"{KEYWORDS_DATABANK_PATH}.tmp"
        with shelve.open(temp_db_path) as temp_db:
            # Load existing keywords
            existing_keywords = temp_db.get('keywords', [])
            # Merge and deduplicate keywords
            all_keywords = list(set(existing_keywords + keywords_bank))
            # Save back to temporary file
            temp_db['keywords'] = all_keywords
        
        # Atomic rename operation
        if os.path.exists(KEYWORDS_DATABANK_PATH):
            os.replace(temp_db_path, KEYWORDS_DATABANK_PATH)
        else:
            os.rename(temp_db_path, KEYWORDS_DATABANK_PATH)
            
        logging.info(f"Successfully updated keywords databank with {len(keywords_bank)} new keywords")
    except Exception as e:
        logging.error(f"Error updating keywords databank: {e}")
        # Clean up temporary file if it exists
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except:
                pass

# function to load files using an extension of unstructured partition with langchain's document loaders
def ExtractText(path: str):
    loader = UnstructuredFileLoader(path, encoding='utf-8')
    documents = loader.load()
    return documents

# function to create metadata keyword tags for document and chunk using OpenAI
def OpenAIMetadataTagger(document: list[Document]):
    
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

    llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")  # Changed to gpt-4o-mini for consistency

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
client = openai.OpenAI(api_key=openai.api_key)
def KeyBERTOpenAIMetadataTagger(document):

    # Create your LLM
    llm = OpenAI(client)
    kw_model = KeyLLM(llm)

    # Load it in KeyLLM
    kw_model = KeyLLM(llm)

    # Extract keywords
    keywords = kw_model.extract_keywords(document,check_vocab=True)

    return keywords

# function to split documents into set smaller chunks for better retrieval processing
# includes overlap to maintain context between chunks
def recursiveChunker(documents: list[Document]):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=400,
        length_function=len,
        add_start_index=True
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # print sample chunks for verification
    print('Example Chunks:')
    print(chunks[0])
    print('='*100)
    print(chunks[1])
    print('='*100)
    print(chunks[2])

    return chunks

# function to split documents into semantic smaller chunks for better retrieval processing
def semanticChunker(documents: list[Document]):

    text_splitter = SemanticChunker(OpenAIEmbeddings())

    chunks = text_splitter.split_documents(documents)

    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # print sample chunks for verification
    #print('Example Chunks:')
    #print(chunks[0])
    #print('='*100)
    #print(chunks[1])
    #print('='*100)
    #print(chunks[2])

    return chunks

# function to split chunks into batches for efficient processing
def batching(chunks, batch_size):

    for i in range(0, len(chunks), batch_size):
        yield chunks[i:i + batch_size]

#Adding documents to the appropriate collection
def databaseInsertion(batches, collection: Chroma):
 
    for chunk in batches:
        collection.add_documents(documents=chunk)

def initialiseDatabase():

    chat_files = glob(CHAT_DATA_PATH + '/**/*.*', recursive=True)
    for file in chat_files:
        dataProcessing(file, collection=chat_db)

    classification_files = glob(CLASSIFICATION_DATA_PATH + '/**/*.*', recursive=True)
    for file in classification_files:
        dataProcessing(file, collection=classification_db)

if __name__ == "__main__":
    pass
