import os
from dotenv import load_dotenv
import openai
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

# Load environment variables from .env file
load_dotenv()
DATABASE_PATH = os.getenv("DATABASE_PATH")
CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)

db = Chroma(
            collection_name="chat", 
            embedding_function=embedding,
            persist_directory=DATABASE_PATH,
        )



