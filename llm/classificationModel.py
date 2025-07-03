#!/usr/bin/env python3
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
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
from infra_utils import get_chatbot_dir

# Constants
load_dotenv()
DATABASE_PATH = os.path.abspath(
    os.path.join(get_chatbot_dir(), os.getenv("DATABASE_PATH", ""))
)
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")

# Initialize components
llm = ChatOpenAI(temperature=0.8, model="gpt-4o-mini")
embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
from backend.database import get_duckdb_collection

db = get_duckdb_collection("classification")

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
    retriever=db.as_retriever(search_kwargs={"k": 3}),
    llm=llm,
    prompt=multi_query_template,
)

# Enhanced system prompt with detailed NYP CNC information
system_prompt = (
    "You are the NYP FYP CNC Chatbot's classification system, designed to help NYP (Nanyang Polytechnic) staff and students identify and use the correct sensitivity labels in their communications. "
    "## Your Role\n"
    "You are an expert assistant for classifying the security level and sensitivity of text content within the NYP environment. "
    "Your primary goal is to ensure proper information handling and data security compliance. "
    "## Data Security Classification Levels\n"
    "Classify the text into one of the following security categories:\n"
    "1. **Official (Open)**: Public information, no restrictions, can be shared freely\n"
    "2. **Official (Closed)**: Internal information, limited distribution within NYP\n"
    "3. **Restricted**: Sensitive information, need-to-know basis, requires authorization\n"
    "4. **Confidential**: Highly sensitive, authorized personnel only, strict handling\n"
    "5. **Secret**: Critical information, strict access controls, special handling\n"
    "6. **Top Secret**: Highest classification, extremely limited access, maximum security\n"
    "## Sensitivity Categories\n"
    "Also classify the sensitivity of the content into one of the following:\n"
    "- **Non-Sensitive**: No special handling required, standard procedures\n"
    "- **Sensitive Normal**: Standard security measures, routine protection\n"
    "- **Sensitive High**: Enhanced security protocols, special attention required\n"
    "## Classification Guidelines\n"
    "- Use ONLY the following pieces of retrieved context to classify the text\n"
    "- Classify conservatively at a higher security or sensitivity level if unsure\n"
    "- The explicit content of the file should take precedence over surrounding context\n"
    "- Consider the context and potential impact of information disclosure\n"
    "- Avoid giving any harmful, inappropriate, or biased classifications\n"
    "- Respond respectfully and ethically\n"
    "- Do not classify inappropriate or harmful content\n"
    "## Output Format\n"
    "Provide your classification in JSON format with the following structure:\n"
    '{{"classification": "security_level", "sensitivity": "sensitivity_level", "reasoning": "detailed_explanation"}}\n'
    "Keep the classification concise but thorough.\n\n"
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
    print(f"Run time: {end - start} seconds")
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


def classify_text(text: str, config: dict = config) -> dict:
    """
    Classify the given text using the classification workflow.

    :param text: The text to classify.
    :type text: str
    :param config: Configuration dictionary for the workflow.
    :type config: dict
    :return: The classification response.
    :rtype: dict
    """
    state = {"input": text, "context": "", "answer": ""}
    response = classify.invoke(state, config=config)
    return response
