# --- Workflow Re-initialization for Dependency Injection ---
def initialize_classification_workflow():
    """
    (Re)initialize the classification workflow after llm, embedding, and db are injected.
    Call this after setting classificationModel.llm, .embedding, and .db in app.py.
    """
    global multiquery_retriever, classification_chain, rag_chain, workflow, classify
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
    memory = MemorySaver()
    workflow = None
    classify = None
    if rag_chain:
        from langgraph.graph import StateGraph

        workflow = StateGraph(state_schema=State)
        workflow.add_edge(START, "model")
        workflow.add_node("model", call_model)
        classify = workflow.compile(checkpointer=memory)


#!/usr/bin/env python3
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
from typing import Optional
from keyword_cache import filter_filler_words


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

multiquery_retriever = None
if db and llm:
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
    "- Use ONLY the following pieces of retrieved context to classify the text\n"
    "- The explicit content of the file should take precedence over surrounding context\n"
    "- **PRIORITIZE the following extracted keywords** when making your classification decision, "
    "using them to focus on the core topics of the text, in conjunction with the retrieved context:\n"
    "Keywords: {keywords_for_classification}\n"
    "- Consider the context and potential impact of information disclosure\n"
    "{context}"
)

# Creating the prompt template for classification
classification_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)


classification_chain = None
rag_chain = None
if llm and multiquery_retriever:
    classification_chain = create_stuff_documents_chain(llm, classification_prompt)
    rag_chain = create_retrieval_chain(multiquery_retriever, classification_chain)


class State(TypedDict):
    input: str
    keywords_for_classification: str  # New field for your top 20 words string
    context: str
    answer: str


def call_model(state: State):
    if not rag_chain:  # rag_chain here is create_retrieval_chain(multiquery_retriever, classification_chain)
        raise RuntimeError("RAG chain not initialized...")
    start = time.time()
    # Pass the original input for retrieval, but add keywords for the *final* prompt
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


memory = MemorySaver()

workflow = None
classify = None
if rag_chain:
    workflow = StateGraph(state_schema=State)
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    classify = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "Classification"}}


def classify_text(
    text: str, config: dict = config, keywords: Optional[str] = None
) -> dict:
    """
    Classify the given text using the classification workflow. If 'keywords' is provided, classify only the filtered keyword string(s).

    :param text: The text to classify.
    :type text: str
    :param config: Configuration dictionary for the workflow.
    :type config: dict
    :param keywords: Optional filtered keyword string(s) to classify instead of the full text.
    :type keywords: Optional[str]
    :return: The classification response.
    :rtype: dict
    :raises RuntimeError: If the classification workflow is not initialized.
    """
    if not classify:
        raise RuntimeError(
            "Classification workflow not initialized. Ensure LLM and DB are set up in app.py."
        )

    # Apply keyword filtering to the *original content* for RAG
    # This filtered_content will be used for MultiQueryRetriever
    rag_input_content = filter_filler_words(text)  # Assuming filter_filler_words exists

    # Generate top 20 keywords from the original content (as per your new logic)
    # Assuming YAKEMetadataTagger and your keyword processing is here
    from llm.dataProcessing import YAKEMetadataTagger
    import collections

    yake_keywords = YAKEMetadataTagger(
        rag_input_content
    )  # Process the content used for RAG
    all_words = []
    for kw in yake_keywords:
        # Decide if you're taking individual words or phrases from YAKE
        all_words.extend(
            [w.lower() for w in kw.split() if len(w) > 2]
        )  # Example: individual words
        # Or all_words.append(kw.lower()) if you want to keep phrases

    word_counts = collections.Counter(all_words)
    top_20_words_list = [w for w, _ in word_counts.most_common(20)]
    keywords_str_for_llm = ", ".join(top_20_words_list)  # String for LLM

    state = {
        "input": rag_input_content,  # <-- Pass the (filtered) file content for RAG
        "keywords_for_classification": keywords_str_for_llm,  # <-- Pass your processed keywords
        "context": "",
        "answer": "",
    }
    response = classify.invoke(state, config=config)
    return response
