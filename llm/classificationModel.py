#!/usr/bin/env python3
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
import openai
import os
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from typing_extensions import TypedDict
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.prompts import PromptTemplate
import time
from utils import get_chatbot_dir

# Constants
load_dotenv()
DATABASE_PATH = os.path.abspath(os.path.join(get_chatbot_dir(), os.getenv('DATABASE_PATH', '')))
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', '')

# Initialize components
llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
db = Chroma(
    collection_name="classification",
    embedding_function=embedding,
    persist_directory=DATABASE_PATH,
)

# Define prompt templates
multi_query_template = PromptTemplate(
    template=(
        "The user has provided the text content of a file: {question}.\n"
        "1. First, check if the text contains multiple sections or topics. "
        "If yes, split the text into distinct sections if there are multiple and move on to point 2."
        "Else, just return the text, and break.\n"
        "2. Then, for each distinct section, generate 3 rephrasings that would return "
        "similar but slightly different relevant results.\n"
        "Return each section on a new line with its rephrasings.\n"
    ),
    input_variables=["question"],
)
multiquery_retriever = MultiQueryRetriever.from_llm(
    retriever=db.as_retriever(search_kwargs={'k': 3}),
    llm=llm,
    prompt=multi_query_template
)

# Adjusted system prompt to include the context variable
system_prompt = (
    "You are an assistant for classifying the security level and sensitivity of text content. "
    "Use ONLY the following pieces of retrieved context to classify the text. "
    "Classify the following text and avoid giving any harmful, inappropriate, or biased content. "
    "Respond respectfully and ethically. Do not classify inappropriate or harmful content. "
    "Classify the text into one of the following security categories: Official(Open), Official(Closed), Restricted, Confidential, Secret or Top Secret. "
    "Also classify the sensitivity of the content into one of the following: Sensitive High, Sensitive Normal, or Non-Sensitive. "
    "Classify conservatively at a higher security or sensitivity level if unsure, to avoid potential risks. "
    "The explicit content of the file should take precedence over the surrounding context when classifying. "
    "Explain your reasoning based on the file contents. "
    "Keep the classification concise. "
    "The output should be in a JSON format with \"classification\", \"sensitivity\", and \"reasoning\"."
    "\n\n"
    "{context}"
)

# Creating the prompt template for classification
classification_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

# Create the classification chain with multi-query retriever
classification_chain = create_stuff_documents_chain(llm, classification_prompt)
rag_chain = create_retrieval_chain(multiquery_retriever, classification_chain)

class State(TypedDict):
    input: str
    context: str
    answer: str

def call_model(state: State):
    start = time.time()
    response = rag_chain.invoke(state)
    end = time.time()
    print(f'Run time: {end-start} seconds')
    return {
        "context": response["context"],
        "answer": response["answer"],
    }

workflow = StateGraph(state_schema=State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
memory = MemorySaver()
classify = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "Classification"}}

def classify_text(text, config=config):
    state = {"input": text, "context": "", "answer": ""}
    response = classify.invoke(state, config=config)
    return response
