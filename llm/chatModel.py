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
from typing import Sequence
import openai, os, json, shelve
import sqlite3
from typing import cast # Import 'cast' for type hinting
from openai.types.chat import ChatCompletionToolParam 
from openai.types import FunctionDefinition
from dotenv import load_dotenv
from utils import rel2abspath, create_folders

load_dotenv()

# Environment setup
DATABASE_PATH = os.getenv("DATABASE_PATH")
CHAT_DATA_PATH = os.getenv("CHAT_DATA_PATH")
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
KEYWORDS_DATABANK_PATH = rel2abspath(os.getenv("KEYWORDS_DATABANK_PATH", ''))
LANGCHAIN_CHECKPOINT_PATH = rel2abspath(os.getenv("LANGCHAIN_CHECKPOINT_PATH", ''))

create_folders(LANGCHAIN_CHECKPOINT_PATH)

llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)

# Load main vector DB
db = Chroma(
    collection_name="chat",
    embedding_function=embedding,
    persist_directory=DATABASE_PATH,
)

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
        ("system", "Reformulate standalone questions from the chat history."),
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

def match_keywords(question):
    with shelve.open(KEYWORDS_DATABANK_PATH) as db:
        keywords = db['keywords']
    keywords.append('None')
    content = f"""###Keywords###
    {', '.join(keywords)}

    ###Instructions###
    From the list of keywords, select all that apply to the question’s topic or subject matter. If no keywords apply, return an empty list for 'prediction'.
    {question}
    """
    function_definition: ChatCompletionToolParam = cast(ChatCompletionToolParam, {
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
    })

    # Assuming 'openai' is an imported client instance (e.g., from openai import OpenAI; client = OpenAI(); client.chat.completions.create...)
    # If 'openai' is the top-level library object, the call below is fine.
    r = openai.chat.completions.create(
        model="gpt-4",
        temperature=0.0,
        messages=[{"role": "user", "content": content}],
        tools=[function_definition],
        tool_choice={"type": "function", "function": {"name": "match_keywords"}}
    )
    predictions = [] # Initialize predictions to an empty list
    if r.choices and r.choices[0].message.tool_calls:
        # Access the list of tool calls. Since we forced a specific tool_choice,
        # we expect exactly one tool call here.
        first_tool_call = r.choices[0].message.tool_calls[0]

        # Check if it's indeed a function tool call and the correct function
        if first_tool_call.type == "function" and first_tool_call.function.name == "match_keywords":
            args_str = first_tool_call.function.arguments

            try:
                # Parse the JSON string into a Python dictionary
                parsed_args = json.loads(args_str)
                predictions = parsed_args.get("prediction", []) # Safely get 'prediction', default to empty list
                print(f"Extracted predictions: {predictions}") # For debugging
            except json.JSONDecodeError as e:
                print(f"Error parsing function arguments JSON: {e}")
                print(f"Raw arguments string: {args_str}") # Print raw string to help debug malformed JSON
        else:
            print("Unexpected tool call type or function name in response.")
    else:
        print("No tool calls found in the OpenAI response message.")


def build_keyword_filter(matched_keywords, max_keywords=10):
    return {
        "$or": [
            {f"keyword{i}": {"$in": matched_keywords}}
            for i in range(max_keywords)
        ]
    }


def route_retriever(question):
    matched_keywords = match_keywords(question)
        
    if not matched_keywords: 
        print("No keywords matched, returning default retriever.") # Added for debugging/clarity
        return db.as_retriever(search_kwargs={'k': 5})
    keyword_filter = build_keyword_filter(matched_keywords)
    return db.as_retriever(search_kwargs={'k': 5, 'filter': keyword_filter})

class State(TypedDict):
    input: str
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    answer: str

def call_model(state: State):
    question = state["input"]
    retriever = route_retriever(question)

    multiquery_retriever_with_keyword = MultiQueryRetriever.from_llm(
        retriever=retriever,
        llm=llm,
        prompt=multi_query_template
    )

    multiquery_retriever = MultiQueryRetriever.from_llm(
        retriever=db.as_retriever(search_kwargs={'k': 5}),
        llm=llm,
        prompt=multi_query_template
    )

    ensemble_retriever = EnsembleRetriever(
    retrievers=[multiquery_retriever, multiquery_retriever_with_keyword], weights=[0.75, 0.25]
    )

    history_aware_retriever = create_history_aware_retriever(
        llm, ensemble_retriever, contextualize_q_prompt
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    response = rag_chain.invoke(state)      
    return {
        "chat_history": [
            HumanMessage(state["input"]),
            AIMessage(response["answer"]),
        ],
        "context": response["context"],
        "answer": response["answer"],
    }

workflow = StateGraph(state_schema=State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
conn = sqlite3.connect(LANGCHAIN_CHECKPOINT_PATH, check_same_thread=False)
sqlite_saver = SqliteSaver(conn)  
app = workflow.compile(checkpointer=sqlite_saver)

def get_convo_hist_answer(question, thread_id):
    state = {"input": question, "chat_history": [], "context": "", "answer": ""}
    return app.invoke(state, config={"configurable": {"thread_id": thread_id}})