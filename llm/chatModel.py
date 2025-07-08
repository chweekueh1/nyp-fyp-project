# llm/chatModel.py
#!/usr/bin/env python3
# llm/chatModel.py
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain.prompts import PromptTemplate
from typing import Sequence, List, Any, Optional, Dict, TypedDict
import openai
import os
import json
import aiosqlite  # <--- ADD THIS IMPORT
from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params import FunctionDefinition
from dotenv import load_dotenv
from infra_utils import (
    rel2abspath,
    create_folders,
)
import logging
import threading
from llm.keyword_cache import get_cached_response, set_cached_response
from system_prompts import (
    get_chat_prompt_template,
    get_chat_contextual_sys_prompt,
    get_chat_system_prompt,
)

# Set up logging for this specific module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - (chatModel.py) - %(message)s",
)

load_dotenv()

# --- Environment Setup and Path Resolution ---
BASE_CHATBOT_DIR = str(os.getcwd())

default_db_path = os.path.join("data", "vector_store", "chroma_db")
DATABASE_PATH = rel2abspath(
    os.path.join(BASE_CHATBOT_DIR, os.getenv("DATABASE_PATH", default_db_path))
)

default_keyword_path = os.path.join("data", "keyword", "keywords_databank")
KEYWORDS_DATABANK_PATH = rel2abspath(
    os.path.join(
        BASE_CHATBOT_DIR, os.getenv("KEYWORDS_DATABANK_PATH", default_keyword_path)
    )
)

default_langchain_path = os.path.join("data", "memory_persistence", "checkpoint.sqlite")
LANGCHAIN_CHECKPOINT_PATH = rel2abspath(
    os.path.join(
        BASE_CHATBOT_DIR, os.getenv("LANGCHAIN_CHECKPOINT_PATH", default_langchain_path)
    )
)

# Define CACHE_DIR before it's used
CACHE_DIR = os.path.join(BASE_CHATBOT_DIR, "data", "cache")

# Use capital letters for the API key variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

llm: Optional[ChatOpenAI] = None
embedding: Optional[OpenAIEmbeddings] = None
client: Optional[openai.OpenAI] = None
db: Optional[Any] = None
app = None
llm_init_lock = threading.Lock()


async def initialize_llm_and_db() -> None:
    """
    Initialize LLM and database with performance optimizations.
    """
    global llm, embedding, client, db, app
    with llm_init_lock:
        if (
            llm is not None
            and embedding is not None
            and client is not None
            and db is not None
            and app is not None
        ):
            logging.info("LLM and DB already initialized, skipping...")
            return

        if not OPENAI_API_KEY:
            logging.critical(
                "OPENAI_API_KEY environment variable not set. Chat features will not work."
            )
            llm = None
            embedding = None
            client = None
            db = None
            app = None
            return

        try:
            # Ensure necessary directories exist for persistent storage
            try:
                create_folders(os.path.dirname(DATABASE_PATH))
                create_folders(os.path.dirname(KEYWORDS_DATABANK_PATH))
                create_folders(os.path.dirname(LANGCHAIN_CHECKPOINT_PATH))
                create_folders(CACHE_DIR)
            except PermissionError as e:
                logging.warning(f"Permission denied creating directories: {e}")
            except Exception as e:
                logging.warning(f"Failed to create directories: {e}")

            logging.info("🤖 Initializing LLM components...")
            llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
            embedding = OpenAIEmbeddings(
                model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
            )
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logging.info("LLM, embedding, and OpenAI client initialized.")

        except Exception as e:
            logging.critical(f"Failed to initialize LLM or client: {e}")
            llm = None
            embedding = None
            client = None
            db = None
            app = None
            return

        try:
            if embedding is None:
                logging.critical(
                    "Embedding model not initialized. Cannot initialize DuckDB vector store."
                )
                db = None
                return

            logging.info("🗄️ Loading DuckDB vector store...")
            from backend.database import get_duckdb_collection

            db = get_duckdb_collection("chat")
            logging.info(f"DuckDB vector store 'chat' loaded from {DATABASE_PATH}")

            try:
                db.get(limit=1)
                logging.info("DuckDB vector store cache test successful.")
            except Exception as cache_e:
                logging.warning(f"DuckDB vector store cache test failed: {cache_e}")
                try:
                    db = get_duckdb_collection("chat")
                    logging.info("Successfully recreated DuckDB vector store.")
                except Exception as recreate_e:
                    logging.error(
                        f"Failed to recreate DuckDB vector store: {recreate_e}"
                    )
                    db = None

        except Exception as e:
            logging.critical(f"Failed to load DuckDB vector store 'chat': {e}")
            db = None

        try:
            missing_components = []
            if not llm:
                missing_components.append("llm")
            if not embedding:
                missing_components.append("embedding")
            if not client:
                missing_components.append("client")
            if not db:
                missing_components.append("db")
            if missing_components:
                logging.critical(
                    f"Cannot initialize LangGraph workflow. Missing: {', '.join(missing_components)}"
                )
                app = None
            else:
                logging.info("🔗 Initializing LangGraph workflow...")
                await _initialize_langgraph_workflow()
                logging.info("LangGraph workflow initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize LangGraph workflow: {e}")
            app = None

        if llm and embedding and client and db and app:
            logging.info(
                "LLM, DuckDB vector store, OpenAI client, and LangGraph app initialized successfully."
            )
        else:
            logging.critical("One or more core components failed to initialize.")


async def _initialize_langgraph_workflow() -> None:
    """
    Initialize the LangGraph workflow for conversational AI.
    """
    global app

    workflow = StateGraph(state_schema=State)
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")

    try:
        logging.info(f"Attempting to connect to SQLite at: {LANGCHAIN_CHECKPOINT_PATH}")
        # Create a new connection for each compilation to avoid event loop binding issues
        conn = await aiosqlite.connect(LANGCHAIN_CHECKPOINT_PATH)
        sqlite_saver = AsyncSqliteSaver(conn)
        app = workflow.compile(checkpointer=sqlite_saver)
        # Close the connection after compilation to avoid keeping it bound to the event loop
        await conn.close()
        logging.info(
            f"LangGraph workflow compiled with checkpointing at {LANGCHAIN_CHECKPOINT_PATH}"
        )
    except Exception as e:
        logging.warning(f"Failed to connect to SQLite checkpoint: {e}")
        app = workflow.compile()
        logging.warning(
            "LangGraph compiled without checkpointing. State will not persist across runs."
        )


def is_llm_ready() -> bool:
    return llm is not None and db is not None and client is not None and app is not None


# --- Prompt Templates ---
multi_query_template = PromptTemplate(
    template=get_chat_prompt_template(),
    input_variables=["question"],
)

contextualize_q_system_prompt = get_chat_contextual_sys_prompt()

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

system_prompt = get_chat_system_prompt()

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


# --- Keyword Matching Function ---
def match_keywords(question: str) -> List[str]:
    if not question:
        return []
    cached = get_cached_response(question)
    if cached is not None:
        try:
            predictions = json.loads(cached)
            if isinstance(predictions, list):
                return predictions
        except Exception:
            pass
    try:
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
                            "description": "List of matched keywords",
                        }
                    },
                    "required": ["prediction"],
                },
            ),
        )

        if client is None:
            logging.error("OpenAI client not initialized")
            return []

        r = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "user",
                    "content": f"Match the following question to relevant keywords: {question}",
                }
            ],
            tools=[tool_param],
            tool_choice={"type": "function", "function": {"name": "match_keywords"}},
        )
        predictions = _extract_predictions_from_response(r, question)
        set_cached_response(question, json.dumps(predictions))
        return predictions
    except openai.APIError as e:
        logging.error(
            f"OpenAI API error during keyword matching for '{question}': {e}",
            exc_info=True,
        )
        return []
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during keyword matching for '{question}': {e}",
            exc_info=True,
        )
        return []


def _extract_predictions_from_response(r: Any, question: str) -> List[str]:
    predictions = []
    if r.choices and r.choices[0].message.tool_calls:
        first_tool_call = r.choices[0].message.tool_calls[0]
        if (
            first_tool_call.type == "function"
            and first_tool_call.function.name == "match_keywords"
        ):
            args_str = first_tool_call.function.arguments
            try:
                parsed_args = json.loads(args_str)
                predictions = parsed_args.get("prediction", [])
                if "no_keywords_matched" in predictions:
                    predictions.remove("no_keywords_matched")
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing tool call arguments: {e}")
    return predictions


def build_keyword_filter(
    matched_keywords: List[str], max_keywords: int = 10
) -> Dict[str, Any]:
    """
    Builds a ChromaDB filter dictionary for given keywords.
    Assumes keywords are stored in metadata fields like 'keyword0', 'keyword1', etc.
    """
    if not matched_keywords:
        return {}

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
        logging.error(
            "DuckDB vector store not initialized. Cannot route retriever. Returning None."
        )
        return None

    matched_keywords = match_keywords(question)

    if not matched_keywords:
        logging.info("No keywords matched for routing, returning default retriever.")
        if db:
            return db.as_retriever(search_kwargs={"k": 5})
        else:
            logging.error("db is None in route_retriever's default path.")
            return None

    keyword_filter = build_keyword_filter(matched_keywords)
    logging.info(
        f"Keywords matched: {matched_keywords}. Applying filter: {keyword_filter}."
    )
    if db:
        return db.as_retriever(
            search_kwargs={"k": 5, "filter": {"keywords": matched_keywords}}
        )
    else:
        logging.error("db is None in route_retriever's filtered path.")
        return None


# --- LangGraph State and Nodes ---
class State(TypedDict):
    input: str
    chat_history: Sequence[BaseMessage]
    context: str
    answer: str


async def call_model(state: State) -> State:
    """Call the model with the given state."""
    if llm is None:
        logging.error("LLM not initialized")
        return _error_state(
            state["input"],
            state["chat_history"],
            "AI not ready",
            "No context due to initialization error.",
        )
    try:
        messages = qa_prompt.format_messages(
            input=state["input"],
            chat_history=state["chat_history"],
            context=state.get("context", ""),
        )
        response = await llm.ainvoke(messages)
        if not response or not response.content:
            return _error_state(
                state["input"],
                state["chat_history"],
                "No response from model",
                "No context available.",
            )
        return {
            "input": str(state["input"]),
            "chat_history": state["chat_history"],
            "context": str(state["context"]),
            "answer": str(response.content),
        }
    except Exception as e:
        logging.error(f"Error in model call: {e}")
        return _error_state(
            state["input"],
            state["chat_history"],
            "Sorry, I encountered an error. Please try again.",
            "Error during model call.",
        )


def _error_state(
    question: str, chat_history: Sequence[BaseMessage], answer: str, context: str
) -> State:
    """Create an error state."""
    return {
        "input": str(question),
        "chat_history": chat_history,
        "context": str(context),
        "answer": str(answer),
    }


# --- Main Answer Retrieval Function ---
async def get_convo_hist_answer(question: str, thread_id: str) -> Dict[str, str]:
    """
    Retrieves a conversational answer using the LangGraph RAG workflow.
    """
    print(
        f"[DEBUG] chatModel.get_convo_hist_answer called with question: {question}, thread_id: {thread_id}"
    )

    if app is None:
        logging.error(
            "LangGraph app is not compiled. Cannot get conversational answer."
        )
        return {
            "answer": "I'm sorry, the AI assistant is not fully set up. Please try again later.",
            "context": "",
        }

    if llm is None or db is None:
        logging.error("LLM or Chroma DB not initialized. Cannot answer question.")
        return {
            "answer": "I'm sorry, I cannot process your request right now due to an internal system error (AI not ready).",
            "context": "No context due to initialization error.",
        }

    initial_state: State = {
        "input": question,
        "chat_history": [],
        "context": "",
        "answer": "",
    }

    try:
        # Create a new SQLite connection for this specific call to avoid event loop binding issues
        conn = await aiosqlite.connect(LANGCHAIN_CHECKPOINT_PATH)
        sqlite_saver = AsyncSqliteSaver(conn)

        # Create a new app instance with the fresh connection
        workflow = StateGraph(state_schema=State)
        workflow.add_node("model", call_model)
        workflow.add_edge(START, "model")
        temp_app = workflow.compile(checkpointer=sqlite_saver)

        result = await temp_app.ainvoke(
            initial_state, config={"configurable": {"thread_id": thread_id}}
        )

        # Close the connection after use
        await conn.close()

        answer = result.get("answer", "No answer generated.")
        context = result.get("context", "No context retrieved.")

        print(f"[DEBUG] chatModel.get_convo_hist_answer returning: {result}")
        return {"answer": answer, "context": context}
    except Exception as e:
        print(f"[ERROR] chatModel.get_convo_hist_answer exception: {e}")
        logging.error(
            f"Error invoking LangGraph workflow for thread '{thread_id}': {e}",
            exc_info=True,
        )
        return {
            "answer": "I'm sorry, I encountered an error while processing your request. Please try again.",
            "context": "",
        }
