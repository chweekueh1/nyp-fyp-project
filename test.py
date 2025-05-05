import shelve
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from typing_extensions import Annotated, TypedDict
from typing import Sequence
import openai, os, json, shelve
from dotenv import load_dotenv

load_dotenv()

# Environment setup
DATABASE_PATH = os.getenv("DATABASE_PATH")
CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)

# Load main vector DB
db = Chroma(
    collection_name="chat",
    embedding_function=embedding,
    persist_directory=DATABASE_PATH,
)

# Keyword matcher (OpenAI function call based)
def match_keywords(question):
    with shelve.open('keywords_databank') as db:
        keywords = db['keywords']
    keywords.append('None')
    content = f"###Keywords###\n{', '.join(keywords)}\n\n###Instructions###\nFrom the list of keywords, select all that apply to the question’s topic or subject matter. If none apply, return 'None'.\n{question}\n"
    function = {
        "name": "match_keywords",
        "description": "Match the question to keywords.",
        "parameters": {
            "type": "object",
            "properties": {
                "prediction": {
                    "type": "array",
                    "items": {"type": "string", "enum": keywords},
                    "description": "Predicted keywords"
                }
            },
            "required": ["prediction"]
        }
    }
    r = openai.chat.completions.create(
        model="gpt-4",
        temperature=0.0,
        messages=[{"role": "user", "content": content}],
        functions=[function],
        function_call={"name": "match_keywords"},
    )
    args_str = r.choices[0].message.function_call.arguments
    args = json.loads(args_str)
    prediction = args['prediction']
    list_prediction = prediction.split(', ')

    return list_prediction

print(match_keywords('what is a phishig email'))