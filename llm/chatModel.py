#!/usr/bin/env python3
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
from typing_extensions import Annotated, TypedDict
from typing import Sequence, List, Any, Optional, Dict, Union, cast
import openai
import os
import json
import shelve
import sqlite3
from openai.types.chat import ChatCompletionToolParam 
from openai.types.shared_params import FunctionDefinition 
from dotenv import load_dotenv
from utils import rel2abspath, create_folders, get_chatbot_dir # Ensure get_chatbot_dir is imported
import logging # Added for internal logging in this file
import pickle
import dill  # For better serialization support
import threading

# Set up logging for this specific module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - (chatModel.py) - %(message)s'
)

load_dotenv()

# --- Environment Setup and Path Resolution ---
# Ensure get_chatbot_dir() returns a string for os.path.join compatibility
BASE_CHATBOT_DIR = str(os.getcwd())

default_db_path = os.path.join("data", "vector_store", "chroma_db")
DATABASE_PATH = rel2abspath(os.path.join(BASE_CHATBOT_DIR, os.getenv("DATABASE_PATH", default_db_path)))

default_keyword_path = os.path.join("data", "keyword", "keywords_databank")
KEYWORDS_DATABANK_PATH = rel2abspath(os.path.join(BASE_CHATBOT_DIR, os.getenv("KEYWORDS_DATABANK_PATH", default_keyword_path))) 

default_langchain_path = os.path.join("data", "memory_persistence", "checkpoint.sqlite")
LANGCHAIN_CHECKPOINT_PATH = rel2abspath(os.path.join(BASE_CHATBOT_DIR, os.getenv("LANGCHAIN_CHECKPOINT_PATH", default_langchain_path))) 

# Ensure necessary directories exist for persistent storage *before* use
create_folders(os.path.dirname(DATABASE_PATH)) # For Chroma DB
create_folders(os.path.dirname(KEYWORDS_DATABANK_PATH)) # For Shelve DB (it's a file, but its directory must exist)
create_folders(os.path.dirname(LANGCHAIN_CHECKPOINT_PATH)) # For LangGraph Checkpoint DB

# Use capital letters for the API key variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", '')

llm: Optional[ChatOpenAI] = None
embedding: Optional[OpenAIEmbeddings] = None
client: Optional[openai.OpenAI] = None
db: Optional[Chroma] = None
app = None  # LangGraph workflow app
llm_init_lock = threading.Lock()

def initialize_llm_and_db():
    """Initialize LLM and database with performance optimizations."""
    global llm, embedding, client, db, app
    with llm_init_lock:
        # Skip if already initialized
        if llm is not None and embedding is not None and client is not None and db is not None and app is not None:
            logging.info("LLM and DB already initialized, skipping...")
            return

        if not OPENAI_API_KEY:
            logging.critical("OPENAI_API_KEY environment variable not set. Chat features will not work.")
            llm = None
            embedding = None
            client = None
            db = None
            return

        try:
            # Initialize core components
            logging.info("🤖 Initializing LLM components...")
            llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
            embedding = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logging.info("LLM, embedding, and OpenAI client initialized.")

        except Exception as e:
            logging.critical(f"Failed to initialize LLM or client: {e}")
            llm = None
            embedding = None
            client = None
            db = None
            return

        # Load Chroma DB with caching
        try:
            if embedding is None:
                logging.critical("Embedding model not initialized. Cannot initialize Chroma DB.")
                db = None
                return

            logging.info("🗄️ Loading Chroma DB...")
            db = Chroma(
                collection_name="chat",
                embedding_function=embedding,
                persist_directory=DATABASE_PATH,
            )
            logging.info(f"Chroma DB 'chat' loaded from {DATABASE_PATH}")

            # Cache the database for faster subsequent loads
            try:
                # Test the database connection
                db.get(limit=1)
                logging.info("Chroma DB loaded from cache.")
            except Exception as cache_e:
                logging.warning(f"Chroma DB cache test failed: {cache_e}")
                # Try to recreate from existing data
                try:
                    db = Chroma(
                        collection_name="chat",
                        embedding_function=embedding,
                        persist_directory=DATABASE_PATH,
                    )
                    logging.info("Successfully recreated Chroma DB from cache")
                except Exception as recreate_e:
                    logging.error(f"Failed to recreate Chroma DB: {recreate_e}")
                    db = None

        except Exception as e:
            logging.critical(f"Failed to load Chroma DB 'chat': {e}")
            db = None

        # Initialize LangGraph workflow
        try:
            if llm and embedding and client and db:
                logging.info("🔗 Initializing LangGraph workflow...")
                _initialize_langgraph_workflow()
                logging.info("LangGraph workflow initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize LangGraph workflow: {e}")
            app = None

        # Save successful initialization state
        if llm and embedding and client and db:
            logging.info("Saved Chroma DB to cache")
            logging.info("LLM, Chroma DB, and OpenAI client initialized successfully.")

def _initialize_langgraph_workflow():
    """Initialize the LangGraph workflow for conversational AI."""
    global app

    # Import required modules
    import sqlite3
    from langgraph.checkpoint.sqlite import SqliteSaver

    # Create the workflow
    workflow = StateGraph(state_schema=State)
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")

    try:
        logging.info(f"Attempting to connect to SQLite at: {LANGCHAIN_CHECKPOINT_PATH}")
        conn = sqlite3.connect(LANGCHAIN_CHECKPOINT_PATH, check_same_thread=False)
        sqlite_saver = SqliteSaver(conn)
        app = workflow.compile(checkpointer=sqlite_saver)
        logging.info(f"LangGraph workflow compiled with checkpointing at {LANGCHAIN_CHECKPOINT_PATH}")
    except Exception as e:
        logging.warning(f"Failed to connect to SQLite checkpoint: {e}")
        app = workflow.compile()  # Compile without checkpointer if it fails
        logging.warning("LangGraph compiled without checkpointing. State will not persist across runs.")

def is_llm_ready() -> bool:
    return llm is not None and db is not None and client is not None and app is not None

# Initialize only when explicitly called, not at module load
# This prevents initialization loops and allows controlled startup

# --- Prompt Templates ---
multi_query_template = PromptTemplate( 
    template=(
        "The user has asked a question: {question}.\n"
        "1. First, check if it is a complex question or multiple related questions. "
        "If yes, split the query into distinct questions if there are multiple and move on to point 2."
        "Else, just return the question, and break.\n"
        "2. Then, for each distinct question, generate 3 rephrasings that would return "
        "similar but slightly different relevant results.\n"
        "Return each question on a new line with its rephrasings.\n"
    ),
    input_variables=["question"],
)

contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use ONLY the following pieces of retrieved context to answer the questions. "
    "Answer the following question and avoid giving any harmful, inappropriate, or biased content. "
    "Respond respectfully and ethically. Do not answer inappropriate or harmful questions. "
    "If the answer does not exist in the vector database, "
    "Use your best judgment to answer the question if you feel the question is still related to NYP CNC and data security. "
    "Otherwise, reject the question nicely."
    "Keep the answer concise."
    "\n\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# --- Keyword Matching Function ---
def match_keywords(question: str) -> List[str]:
    if not question:
        return []
    try:
        # Define the function parameter for keyword matching
        tool_param = ChatCompletionToolParam(
            type="function",
            function=FunctionDefinition(
                name="match_keywords",
                description="Match the question to relevant keywords",
                parameters={
                    "type": "object",
                    "properties": {
                        "prediction": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of matched keywords"
                        }
                    },
                    "required": ["prediction"]
                }
            )
        )
        
        if client is None:
            logging.error("OpenAI client not initialized")
            return []
            
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[{"role": "user", "content": f"Match the following question to relevant keywords: {question}"}],
            tools=[tool_param],
            tool_choice={"type": "function", "function": {"name": "match_keywords"}}
        )
        predictions = _extract_predictions_from_response(r, question)
        return predictions
    except openai.APIError as e:
        logging.error(f"OpenAI API error during keyword matching for '{question}': {e}", exc_info=True)
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred during keyword matching for '{question}': {e}", exc_info=True)
        return []

def _extract_predictions_from_response(r: Any, question: str) -> List[str]:
    predictions = []
    if r.choices and r.choices[0].message.tool_calls:
        first_tool_call = r.choices[0].message.tool_calls[0]
        if first_tool_call.type == "function" and first_tool_call.function.name == "match_keywords":
            args_str = first_tool_call.function.arguments
            try:
                parsed_args = json.loads(args_str)
                predictions = parsed_args.get("prediction", [])
                if "no_keywords_matched" in predictions:
                    predictions.remove("no_keywords_matched")
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing tool call arguments: {e}")
    return predictions

def build_keyword_filter(matched_keywords: List[str], max_keywords: int = 10) -> Dict[str, Any]:
    """
    Builds a ChromaDB filter dictionary for given keywords.
    Assumes keywords are stored in metadata fields like 'keyword0', 'keyword1', etc.
    """
    if not matched_keywords:
        return {} # No filter if no keywords
        
    filter_clauses = []
    for i in range(max_keywords):
        filter_clauses.append({f"keyword{i}": {"$in": matched_keywords}})
    
    return {"$or": filter_clauses}


# --- Retriever Routing and RAG Chain Definition ---
def route_retriever(question: str) -> Optional[Any]:
    """
    Dynamically selects a retriever based on keyword matching.
    """
    if db is None:
        logging.error("Chroma DB not initialized. Cannot route retriever. Returning None.")
        return None 
    
    matched_keywords = match_keywords(question)
    
    if not matched_keywords: 
        logging.info("No keywords matched for routing, returning default retriever.")
        # Ensure db.as_retriever() is only called if db is not None
        if db:
            return db.as_retriever(search_kwargs={'k': 5})
        else:
            logging.error("db is None in route_retriever's default path.")
            return None
    
    keyword_filter = build_keyword_filter(matched_keywords)
    logging.info(f"Keywords matched: {matched_keywords}. Applying filter: {keyword_filter}.")
    # Ensure db.as_retriever() is only called if db is not None
    if db:
        return db.as_retriever(search_kwargs={'k': 5, 'filter': keyword_filter})
    else:
        logging.error("db is None in route_retriever's filtered path.")
        return None


# --- LangGraph State and Nodes ---
class State(TypedDict):
    input: str # The user's current question
    chat_history: Annotated[Sequence[BaseMessage], add_messages] # Cumulative chat history
    context: str # Retrieved context from RAG
    answer: str # The AI's generated answer

def call_model(state: State) -> State:
    """Call the model with the given state.
    
    Args:
        state: The current state containing input, chat history, context, and answer
        
    Returns:
        Updated state with the model's response
    """
    if llm is None:
        logging.error("LLM not initialized")
        return _error_state(
            state["input"],
            state["chat_history"],
            "AI not ready",
            "No context due to initialization error."
        )
    
    try:
        # Get response from model
        response = llm.invoke(state["input"])
        if not response or not response.content:
            return _error_state(
                state["input"],
                state["chat_history"],
                "No response from model",
                "No context available."
            )
        
        return {
            "input": str(state["input"]),
            "chat_history": state["chat_history"],
            "context": str(state["context"]),
            "answer": str(response.content)
        }
    except Exception as e:
        logging.error(f"Error in model call: {e}")
        return _error_state(
            state["input"],
            state["chat_history"],
            "Sorry, I encountered an error. Please try again.",
            "Error during model call."
        )

def _error_state(question: str, chat_history: Sequence[BaseMessage], answer: str, context: str) -> State:
    """Create an error state.
    
    Args:
        question: The user's question
        chat_history: The chat history
        answer: The error message
        context: The context
        
    Returns:
        Error state
    """
    return {
        "input": str(question),
        "chat_history": chat_history,
        "context": str(context),
        "answer": str(answer)
    }

# --- LangGraph Workflow Setup ---
CACHE_DIR = os.path.join(BASE_CHATBOT_DIR, 'data', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
CHROMA_CACHE_PATH = os.path.join(CACHE_DIR, 'chroma_db.pkl')
LANGCHAIN_CACHE_PATH = os.path.join(CACHE_DIR, 'langchain_workflow.pkl')
CACHE_VERSION = "1.0"  # Add version for cache invalidation

app: Optional[Any] = None # Initialize app to None
# Ensure llm, db, and client are all initialized before compiling the workflow
if llm and db and client:
    logging.info("LLM, Chroma DB, and OpenAI client initialized successfully.")
    # Try to load Chroma DB and LangGraph workflow from cache
    chroma_loaded = False
    workflow_loaded = False
    
    def load_from_cache(cache_path: str, cache_type: str) -> tuple[Optional[Any], bool]:
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    if isinstance(cached_data, dict) and cached_data.get('version') == CACHE_VERSION:
                        return cached_data.get('data'), True
            return None, False
        except Exception as e:
            logging.warning(f"Failed to load {cache_type} from cache: {e}")
            return None, False

    def save_to_cache(cache_path: str, data: Any, cache_type: str) -> None:
        try:
            # For Chroma DB, we only cache the collection name and persist directory
            if isinstance(data, Chroma):
                cache_data = {
                    'collection_name': data._collection.name,
                    'persist_directory': data._persist_directory
                }
            else:
                cache_data = data
                
            with open(cache_path, 'wb') as f:
                pickle.dump({'version': CACHE_VERSION, 'data': cache_data}, f)
            logging.info(f"Saved {cache_type} to cache")
        except Exception as e:
            logging.warning(f"Failed to save {cache_type} to cache: {e}")

    # Load from cache
    prev_db = db
    _db, chroma_loaded = load_from_cache(CHROMA_CACHE_PATH, "Chroma DB")
    if chroma_loaded and _db is not None:
        logging.info("Chroma DB loaded from cache.")
        # Recreate Chroma DB from cached data
        try:
            db = Chroma(
                collection_name=_db['collection_name'],
                embedding_function=embedding,
                persist_directory=_db['persist_directory']
            )
            logging.info("Successfully recreated Chroma DB from cache")
        except Exception as e:
            logging.error(f"Failed to recreate Chroma DB from cache: {e}")
            db = prev_db
    else:
        logging.info("Chroma DB not found in cache, using initialized instance.")
        # db is already initialized above
    
    # Only save Chroma DB metadata to cache, not the full object
    if db is not None:
        save_to_cache(CHROMA_CACHE_PATH, db, "Chroma DB")
else:
    logging.critical("LLM, Chroma DB, or OpenAI client not initialized. Chat functions will be limited.")


# --- Main Answer Retrieval Function ---
def get_convo_hist_answer(question: str, thread_id: str) -> Dict[str, str]:
    """
    Retrieves a conversational answer using the LangGraph RAG workflow.
    """
    print(f"[DEBUG] chatModel.get_convo_hist_answer called with question: {question}, thread_id: {thread_id}")
    
    if app is None:
        logging.error("LangGraph app is not compiled. Cannot get conversational answer.")
        return {"answer": "I'm sorry, the AI assistant is not fully set up. Please try again later.", "context": ""}
    
    if llm is None or db is None:
        logging.error("LLM or Chroma DB not initialized. Cannot answer question.")
        return {"answer": "I'm sorry, I cannot process your request right now due to an internal system error (AI not ready).", "context": "No context due to initialization error."}
        
    # LangGraph's checkpointer automatically loads history based on thread_id
    # We pass the initial 'input' for the current turn.
    # The 'chat_history' will be loaded from the checkpointer by LangGraph based on the thread_id config.
    initial_state: State = {
        "input": question,
        "chat_history": [],
        "context": "",
        "answer": ""
    }

    try:
        result = app.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
        
        answer = result.get("answer", "No answer generated.")
        context = result.get("context", "No context retrieved.")
        
        print(f"[DEBUG] chatModel.get_convo_hist_answer returning: {result}")
        return {"answer": answer, "context": context}
    except Exception as e:
        print(f"[ERROR] chatModel.get_convo_hist_answer exception: {e}")
        logging.error(f"Error invoking LangGraph workflow for thread '{thread_id}': {e}", exc_info=True)
        return {"answer": "I'm sorry, I encountered an error while processing your request. Please try again.", "context": ""}
