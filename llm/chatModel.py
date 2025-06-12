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
from typing import Sequence, List
import openai
import os
import json
import shelve
import sqlite3
from typing import cast # For type hinting
from openai.types.chat import ChatCompletionToolParam 
from openai.types.shared_params import FunctionDefinition 
from dotenv import load_dotenv
from utils import rel2abspath, create_folders, get_chatbot_dir # Ensure get_chatbot_dir is imported
import logging # Added for internal logging in this file

# Set up logging for this specific module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - (chatModel.py) - %(message)s'
)

load_dotenv()

# --- Environment Setup and Path Resolution ---
# Ensure get_chatbot_dir() returns a string for os.path.join compatibility
BASE_CHATBOT_DIR = str(get_chatbot_dir())

DATABASE_PATH = rel2abspath(os.path.join(BASE_CHATBOT_DIR, os.getenv("DATABASE_PATH", "data\\vector_store\\chroma_db")))
KEYWORDS_DATABANK_PATH = rel2abspath(os.path.join(BASE_CHATBOT_DIR, os.getenv("KEYWORDS_DATABANK_PATH", "")))
LANGCHAIN_CHECKPOINT_PATH = rel2abspath(os.path.join(BASE_CHATBOT_DIR, os.getenv("LANGCHAIN_CHECKPOINT_PATH", "")))

# Ensure necessary directories exist for persistent storage *before* use
create_folders(os.path.dirname(DATABASE_PATH)) # For Chroma DB
create_folders(os.path.dirname(KEYWORDS_DATABANK_PATH)) # For Shelve DB (it's a file, but its directory must exist)
create_folders(os.path.dirname(LANGCHAIN_CHECKPOINT_PATH)) # For LangGraph Checkpoint DB

# Use capital letters for the API key variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logging.critical("OPENAI_API_KEY environment variable not set. Chat features will not work.")
    llm = None
    embedding = None
    client = None # Initialize client as None if API key is missing
else:
    llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini") 
    embedding = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    client = openai.OpenAI(api_key=OPENAI_API_KEY) # Initialize the OpenAI client here


# Load main vector DB
db = None # Initialize to None in case of failure
if embedding and DATABASE_PATH:
    try:
        db = Chroma(
            collection_name="chat",
            embedding_function=embedding,
            persist_directory=DATABASE_PATH,
        )
        logging.info(f"Chroma DB 'chat' loaded from {DATABASE_PATH}")
    except Exception as e:
        logging.critical(f"Failed to load Chroma DB 'chat': {e}", exc_info=True)
else:
    logging.critical("Embedding function or DATABASE_PATH is not properly set up. Chroma DB cannot be initialized.")


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
    """
    Matches the question to predefined keywords using OpenAI's function calling.
    """
    if client is None: # Use the global OpenAI client instance
        logging.error("OpenAI client not initialized. Cannot match keywords.")
        return []

    keywords = []
    try:
        # Using shelve.open on the determined path
        with shelve.open(str(KEYWORDS_DATABANK_PATH)) as db_shelf: # Ensure path is string
            keywords = db_shelf.get('keywords', []) 
            if not keywords:
                logging.warning(f"No keywords found in shelve DB at {KEYWORDS_DATABANK_PATH}. Ensure initialiseDatabase() populates it.")
                return []
    except Exception as e:
        logging.error(f"Error opening or reading from keyword shelve DB at {KEYWORDS_DATABANK_PATH}: {e}", exc_info=True)
        return []

    # Filter out empty strings and ensure unique keywords for the enum
    unique_keywords = sorted(list(set(k for k in keywords if k and isinstance(k, str))))

    # Provide a default enum value if no keywords are found, to avoid OpenAI API errors.
    enum_values = unique_keywords if unique_keywords else ["no_keywords_matched"]
    
    # Define the function for the tool
    function_definition: FunctionDefinition = { 
        "name": "match_keywords",
        "description": "Match the question to relevant keywords from a predefined list.",
        "parameters": {
            "type": "object",
            "properties": {
                "prediction": {
                    "type": "array",
                    "items": {"type": "string", "enum": enum_values},
                    "description": "List of keywords predicted to be relevant to the question."
                }
            },
            "required": ["prediction"]
        }
    }

    # Cast the entire tool dictionary to ChatCompletionToolParam
    tool_param: ChatCompletionToolParam = cast(ChatCompletionToolParam, {
        "type": "function", 
        "function": function_definition
    })

    try:
        # Use the global `client` instance for API calls
        r = client.chat.completions.create(
            model="gpt-4o-mini", 
            temperature=0.0,
            messages=[{"role": "user", "content": f"Match the following question to relevant keywords: {question}"}],
            tools=[tool_param], # Pass the casted tool_param here
            tool_choice={"type": "function", "function": {"name": "match_keywords"}}
        )
        
        predictions = []
        if r.choices and r.choices[0].message.tool_calls:
            first_tool_call = r.choices[0].message.tool_calls[0]

            if first_tool_call.type == "function" and first_tool_call.function.name == "match_keywords":
                args_str = first_tool_call.function.arguments
                try:
                    parsed_args = json.loads(args_str)
                    predictions = parsed_args.get("prediction", [])
                    # Filter out the "no_keywords_matched" if it was returned
                    if "no_keywords_matched" in predictions:
                        predictions.remove("no_keywords_matched")
                    logging.info(f"Extracted keyword predictions for '{question}': {predictions}")
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing function arguments JSON for '{question}': {e}", exc_info=True)
                    logging.error(f"Raw arguments string from LLM: {args_str}") 
            else:
                logging.warning(f"Unexpected tool call type or function name in OpenAI response for '{question}'.")
        else:
            logging.warning(f"No tool calls found in the OpenAI response message for keyword matching for '{question}'.")
        
        return predictions

    except openai.APIError as e:
        logging.error(f"OpenAI API error during keyword matching for '{question}': {e}", exc_info=True)
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred during keyword matching for '{question}': {e}", exc_info=True)
        return []


def build_keyword_filter(matched_keywords: List[str], max_keywords: int = 10) -> dict:
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
def route_retriever(question: str):
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
    """
    Retrieves relevant context and generates an answer using the RAG chain.
    """
    question = state["input"]
    chat_history = state["chat_history"]

    if llm is None or db is None:
        logging.error("LLM or Chroma DB not initialized. Cannot answer question.")
        # FIX: Convert chat_history to list before concatenation
        return {
            "input": question, 
            "chat_history": list(chat_history) + [HumanMessage(question), AIMessage("Error: AI assistant not fully initialized.")],
            "context": "No context due to initialization error.",
            "answer": "I'm sorry, I cannot process your request right now due to an internal system error (AI not ready)."
        }

    # Route to the appropriate retriever (with or without keyword filter)
    retriever_with_filter = route_retriever(question)

    if retriever_with_filter is None:
        logging.error("Retriever could not be initialized by route_retriever. Cannot answer question.")
        # FIX: Convert chat_history to list before concatenation
        return {
            "input": question, 
            "chat_history": list(chat_history) + [HumanMessage(question), AIMessage("Error: Retriever not available.")],
            "context": "No context due to retriever error.",
            "answer": "I'm sorry, I cannot process your request right now because the knowledge retrieval system is unavailable."
        }

    # Standard MultiQueryRetriever (without keyword filter)
    # FIX: Ensure db is not None before calling as_retriever
    if db is None:
        logging.error("Chroma DB is unexpectedly None during MultiQueryRetriever setup.")
        return {
            "input": question,
            "chat_history": list(chat_history) + [HumanMessage(question), AIMessage("Error: Knowledge database unavailable.")],
            "context": "Database not initialized for multi-query.",
            "answer": "I'm sorry, I cannot access the knowledge database right now."
        }

    multiquery_retriever = MultiQueryRetriever.from_llm(
        retriever=db.as_retriever(search_kwargs={'k': 5}),
        llm=llm,
        prompt=multi_query_template
    )

    # Ensemble retriever to combine results from multiple strategies
    ensemble_retriever = EnsembleRetriever(
        retrievers=[multiquery_retriever, retriever_with_filter], 
        weights=[0.75, 0.25] 
    )

    # History-aware retriever to reformulate queries based on chat history
    history_aware_retriever = create_history_aware_retriever(
        llm, 
        ensemble_retriever, 
        contextualize_q_prompt
    )

    # Chain to combine documents and generate answer
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Full RAG chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    try:
        response = rag_chain.invoke({"input": question, "chat_history": chat_history})
        
        # 'context' from rag_chain is a list of Document objects, convert to string
        retrieved_context = response.get("context", [])
        generated_answer = response.get("answer", "I'm sorry, I couldn't find an answer based on the provided context.")
        
        # Convert context documents to string for storage in state
        context_str = "\n".join([doc.page_content for doc in retrieved_context])
        
        # Return structure aligns with State TypedDict
        # FIX: Convert chat_history to list before concatenation
        return {
            "input": question, 
            "chat_history": list(chat_history) + [HumanMessage(question), AIMessage(generated_answer)],
            "context": context_str,
            "answer": generated_answer,
        }
    except Exception as e:
        logging.error(f"Error during RAG chain invocation for question '{question}': {e}", exc_info=True)
        # Return structure aligns with State TypedDict
        # FIX: Convert chat_history to list before concatenation
        return {
            "input": question, 
            "chat_history": list(chat_history) + [HumanMessage(question), AIMessage("I apologize, but an error occurred while generating my response.")],
            "context": "Error during RAG chain processing.",
            "answer": "I apologize, but an error occurred while generating my response. Please try again."
        }


# --- LangGraph Workflow Setup ---
app = None # Initialize app to None
# Ensure llm, db, and client are all initialized before compiling the workflow
if llm and db and client: 
    workflow = StateGraph(state_schema=State)
    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")

    # Connect to SQLite checkpoint for LangGraph (ensure directory exists)
    try:
        conn = sqlite3.connect(LANGCHAIN_CHECKPOINT_PATH, check_same_thread=False)
        sqlite_saver = SqliteSaver(conn)  
        app = workflow.compile(checkpointer=sqlite_saver)
        logging.info(f"LangGraph workflow compiled with checkpointing at {LANGCHAIN_CHECKPOINT_PATH}")
    except Exception as e:
        logging.critical(f"Failed to connect to SQLite checkpoint or compile LangGraph: {e}", exc_info=True)
        app = workflow.compile() # Compile without checkpointer if it fails
        logging.warning("LangGraph compiled without checkpointing due to error. State will not persist across runs.")
else:
    logging.critical("LLM, Chroma DB, or OpenAI client not initialized. LangGraph workflow will not be compiled. Chat functions will be limited.")


# --- Main Answer Retrieval Function ---
def get_convo_hist_answer(question: str, thread_id: str) -> dict:
    """
    Retrieves a conversational answer using the LangGraph RAG workflow.
    """
    if app is None:
        logging.error("LangGraph app is not compiled. Cannot get conversational answer.")
        return {"answer": "I'm sorry, the AI assistant is not fully set up. Please try again later.", "context": ""}
        
    # LangGraph's checkpointer automatically loads history based on thread_id
    # We pass the initial 'input' for the current turn.
    # The 'chat_history' will be loaded from the checkpointer by LangGraph based on the thread_id config.
    initial_state = {"input": question, "chat_history": []} 

    try:
        result = app.invoke(initial_state, config={"configurable": {"thread_id": thread_id}})
        
        answer = result.get("answer", "No answer generated.")
        context = result.get("context", "No context retrieved.")
        
        return {"answer": answer, "context": context}
    except Exception as e:
        logging.error(f"Error invoking LangGraph workflow for thread '{thread_id}': {e}", exc_info=True)
        return {"answer": "I'm sorry, I encountered an error while processing your request. Please try again.", "context": ""}


