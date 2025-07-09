#!/usr/bin/env python3
import openai
import os
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
import time
from infra_utils import get_chatbot_dir
from typing import Optional, Dict, Any  # noqa: F401
import re  # Import regex module for cleaning


from system_prompts import (
    get_classification_system_prompt,
    get_classification_prompt_template,
)

# Constants
load_dotenv()
DATABASE_PATH = os.path.abspath(
    os.path.join(get_chatbot_dir(), os.getenv("DATABASE_PATH", ""))
)
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "")


# LLM, embedding, and db will be initialized in app.py and injected or imported as needed
llm = None
embedding = None
db = None


# --- Helper Function for Text Cleaning ---
def clean_text_for_classification(text: str) -> str:
    """
    Applies comprehensive cleaning to text to remove redundant symbols,
    markdown, and numerical prefixes, making it suitable for classification.
    """
    if not isinstance(text, str):
        text = str(text)

    # Remove common Markdown headings: e.g., "## Header", "# Title"
    text = re.sub(r"^\s*#+\s*.*$", "", text, flags=re.MULTILINE)
    # Remove horizontal rules: "---", "***"
    text = re.sub(r"^\s*[-*]+\s*$", "", text, flags=re.MULTILINE)
    # Remove list indicators: "1. ", "2. ", "- ", "* "
    text = re.sub(r"^\s*((\d+\.)|[-*])\s+", "", text, flags=re.MULTILINE)
    # Remove redundant spaces and newlines
    text = re.sub(r"\s+", " ", text).strip()
    # Remove any remaining leading/trailing punctuation that might occur after cleaning
    text = re.sub(r"^[.,!?;:()\"']+|[.,!?;:()\"']+$", "", text).strip()
    return text


# --- Workflow Re-initialization for Dependency Injection ---
# Global variables for the workflow components
multiquery_retriever = None
classification_chain = None
rag_chain = None
workflow = None
classify = None
memory = MemorySaver()  # MemorySaver needs to be initialized here


def initialize_classification_workflow():
    """
    (Re)initialize the classification workflow after llm, embedding, and db are injected.
    Call this after setting classificationModel.llm, .embedding, and .db in app.py.
    """
    global \
        multiquery_retriever, \
        classification_chain, \
        rag_chain, \
        workflow, \
        classify, \
        llm, \
        db, \
        multi_query_template, \
        classification_prompt

    # Define prompt templates (re-defined here to ensure they use current system prompts)
    # They should be defined outside this function or passed in if they change dynamically
    # For now, let's assume they pick up the latest get_...() calls when the module loads
    multi_query_template = PromptTemplate(
        template=get_classification_prompt_template(),
        input_variables=["question"],
    )
    system_prompt = get_classification_system_prompt()
    classification_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "{context}\n\n{input}\n\nKeywords for Classification: {keywords_for_classification}",
            ),
        ]
    )

    multiquery_retriever = None
    if db and llm:
        from langchain.retrievers.multi_query import MultiQueryRetriever

        multiquery_retriever = MultiQueryRetriever.from_llm(
            retriever=db.as_retriever(search_kwargs={"k": 3}),
            llm=llm,
            prompt=multi_query_template,
        )

    classification_chain = None
    rag_chain = None
    if llm and multiquery_retriever:
        from langchain.chains.combine_documents import create_stuff_documents_chain
        from langchain.chains import create_retrieval_chain

        classification_chain = create_stuff_documents_chain(llm, classification_prompt)
        rag_chain = create_retrieval_chain(multiquery_retriever, classification_chain)

    global workflow, classify  # Declare globals again to assign
    workflow = None
    classify = None
    if rag_chain:
        from langgraph.graph import StateGraph

        workflow = StateGraph(state_schema=State)
        workflow.add_edge(START, "model")
        workflow.add_node("model", call_model)
        classify = workflow.compile(checkpointer=memory)


# Define prompt templates
# multi_query_template and classification_prompt are now set within initialize_classification_workflow()
# but they need to be globally accessible for initialize_classification_workflow to reference
# or defined outside and passed in. For simplicity, let's define them here and then
# ensure initialize_classification_workflow updates them if they change
multi_query_template_initial = PromptTemplate(
    template=get_classification_prompt_template(),
    input_variables=["question"],
)

system_prompt_initial = get_classification_system_prompt()

classification_prompt_initial = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_initial),
        (
            "human",
            "{context}\n\n{input}\n\nKeywords for Classification: {keywords_for_classification}",
        ),
    ]
)

# Assign to global variables for initial module load (will be overridden by initialize)
multi_query_template = multi_query_template_initial
classification_prompt = classification_prompt_initial


class State(TypedDict):
    input: str
    keywords_for_classification: str  # New field for your top 50 words string
    context: str
    answer: str


def call_model(state: State):
    """
    Calls the RAG chain with the input and keywords for classification.
    """
    global rag_chain  # Ensure rag_chain is accessible
    if not rag_chain:
        raise RuntimeError("RAG chain not initialized...")
    start = time.time()
    response = rag_chain.invoke(
        {
            "input": state["input"],  # Original input for retrieval
            "keywords_for_classification": state[
                "keywords_for_classification"
            ],  # Pass keywords to the final prompt
        }
    )
    end = time.time()
    print(f"Run time: {end - start} seconds")
    return {
        "context": response["context"],
        "answer": response["answer"],
    }


config = {"configurable": {"thread_id": "Classification"}}


def classify_text(
    text: str, config: dict = config, keywords: Optional[str] = None
) -> Dict[str, Any]:
    """
    Classify the given text using the classification workflow.

    This function now expects 'text' to be the already concise and cleaned content
    (e.g., `concise_content_for_llm` from data_classification.py)
    and 'keywords' to be the already processed keyword string
    (e.g., `top_10_str` from data_classification.py).

    :param text: The concise and cleaned content to be used for RAG input.
    :type text: str
    :param config: Configuration dictionary for the workflow.
    :type config: dict
    :param keywords: The processed keyword string (e.g., top 50 words) for the final LLM prompt.
    :type keywords: Optional[str]
    :return: The classification response.
    :rtype: dict
    :raises RuntimeError: If the classification workflow is not initialized.
    """
    global classify  # Ensure classify is accessible
    if not classify:
        raise RuntimeError(
            "Classification workflow not initialized. Ensure LLM and DB are set up in app.py."
        )

    # The 'text' parameter here is expected to already be 'concise_content_for_llm'
    # which has been cleaned and filtered upstream. So no further processing on 'text' itself.
    rag_input_content = text

    # The 'keywords' parameter here is expected to already be 'top_10_str'
    # which has been generated and cleaned upstream.
    keywords_str_for_llm = keywords if keywords is not None else ""

    # Ensure even the input to the state is a string
    rag_input_content = str(rag_input_content)
    keywords_str_for_llm = str(keywords_str_for_llm)

    state = {
        "input": rag_input_content,  # Use the already processed text for RAG
        "keywords_for_classification": keywords_str_for_llm,  # Use the provided keywords
        "context": "",
        "answer": "",
    }
    response = classify.invoke(state, config=config)
    return response
