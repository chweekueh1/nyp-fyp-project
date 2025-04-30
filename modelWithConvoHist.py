# modelWithConvoHist.py

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
import openai
import os
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from typing import Sequence
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate

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

multiquery_retriever = MultiQueryRetriever.from_llm(
    retriever=db.as_retriever(search_kwargs={'k': 3}),
    llm=llm,
    prompt=multi_query_template
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

history_aware_retriever = create_history_aware_retriever(
    llm, multiquery_retriever, contextualize_q_prompt
)

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use ONLY the following pieces of retrieved context to answer the questions. "
    "Answer the following question and avoid giving any harmful, inappropriate, or biased content. "
    "Respond respectfully and ethically. Do not answer inappropriate or harmful questions. "
    "If the answer does not exist in the vector database, "
    "Use your best judgment to answer the question if you feel the question is still related to NYP CNC. "
    "Otherwise, reject the question nicely."
    "Keep the answer concise."
    "\n\n"
    "{context}"
)

# Creating the prompt template for question answering
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create the question-answer chain with multi-query retriever
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

class State(TypedDict):
    input: str
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    answer: str

def get_convo_hist_answer(state: State):
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
workflow.add_node("model", get_convo_hist_answer)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "abc123"}}

def get_convo_hist_answer(question, config=config):
    state = {"input": question, "chat_history": [], "context": "", "answer": ""}
    response = app.invoke(state, config=config)
    return response