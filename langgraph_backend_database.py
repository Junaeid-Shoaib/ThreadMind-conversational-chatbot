# =========================================================
# 1. IMPORTS
# =========================================================
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_unstructured import UnstructuredLoader

import sqlite3
import requests
import os
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import shutil
import streamlit as st


# =========================================================
# 2. ENVIRONMENT SETUP
# =========================================================
load_dotenv()


# =========================================================
# 3. STREAMLIT SECRETS
# =========================================================
# for streamlit secrets
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


# =========================================================
# 4. APP PATHS
# =========================================================
DB_PATH = "chatbot.db"
FAISS_INDEX_PATH = "faiss_index"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# 5. LLM INITIALIZATION
# =========================================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings()


# =========================================================
# 6. RAG / KNOWLEDGE BASE FUNCTIONS
# =========================================================
def load_documents_from_uploads():
    documents = []

    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if os.path.isfile(file_path):
            try:
                loader = UnstructuredLoader(file_path)
                docs = loader.load()

                for doc in docs:
                    doc.metadata["source"] = filename

                documents.extend(docs)
                print(f"Loaded {filename} successfully with {len(docs)} document parts.")

            except Exception as e:
                print(f"Could not load {filename}: {e}")

    print(f"Total loaded document parts: {len(documents)}")
    return documents


def build_vectorstore_from_uploads():
    """
    Build a new FAISS vector store from uploaded files and save it locally.
    """
    documents = load_documents_from_uploads()

    if not documents:
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    split_docs = text_splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)

    return vectorstore


def load_vectorstore():
    """
    Load FAISS index if it exists.
    """
    if os.path.exists(FAISS_INDEX_PATH):
        return FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

    return None


def refresh_vectorstore():
    """
    Rebuild the FAISS index from the current uploads folder.
    """
    global vectorstore, retriever

    vectorstore = build_vectorstore_from_uploads()

    if vectorstore is not None:
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5})
    else:
        retriever = None


def save_uploaded_file(uploaded_file):
    """
    Save uploaded file into the uploads folder, then rebuild vector store.
    """
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    refresh_vectorstore()
    return file_path


def list_uploaded_files():
    """
    Return all uploaded file names.
    """
    return [
        filename
        for filename in os.listdir(UPLOAD_FOLDER)
        if os.path.isfile(os.path.join(UPLOAD_FOLDER, filename))
    ]


def delete_uploaded_file(filename):
    """
    Delete one uploaded file and rebuild the vector store.
    """
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    refresh_vectorstore()


def clear_knowledge_base():
    """
    Remove all uploaded files and FAISS index.
    """
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    if os.path.exists(FAISS_INDEX_PATH):
        shutil.rmtree(FAISS_INDEX_PATH)

    global vectorstore, retriever
    vectorstore = None
    retriever = None


# =========================================================
# 7. INITIAL VECTORSTORE LOAD
# =========================================================
vectorstore = load_vectorstore()

if vectorstore is None:
    vectorstore = build_vectorstore_from_uploads()

if vectorstore is not None:
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
else:
    retriever = None


# =========================================================
# 8. TOOL DEFINITIONS
# =========================================================
@tool
def brave_search(query: str) -> str:
    """
    Search the web using Brave Search API.
    """
    api_key = os.getenv("BRAVE_API_KEY")

    url = "https://api.search.brave.com/res/v1/web/search"

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }

    params = {
        "q": query,
        "count": 1
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    results = data.get("web", {}).get("results", [])

    if not results:
        return "No results found"

    return f"{results[0]['title']} - {results[0]['description']}"


@tool
def calculator(firstnum: float, secondnum: float, operation: str) -> dict:
    """
    Perform basic arithmetic operations on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = firstnum + secondnum
        elif operation == "sub":
            result = firstnum - secondnum
        elif operation == "mul":
            result = firstnum * secondnum
        elif operation == "div":
            if secondnum == 0:
                return {"error": "Division by zero is not allowed."}
            result = firstnum / secondnum
        else:
            return {"error": f"Unsupported operation: {operation}"}

        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Get the current stock price for a given symbol using Alpha Vantage.
    Input should be a stock ticker (e.g., 'AAPL', 'IBM').
    """

    api_key = os.getenv("STOCK_API_KEY")
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    r = requests.get(url)
    data = r.json()
    return data


@tool
def rag_search(query: str) -> str:
    """
    Search the internal knowledge base built from uploaded files.
    """
    if retriever is None:
        return "No uploaded documents are available in the knowledge base yet."

    docs = retriever.invoke(query)

    if not docs:
        return "No relevant information found in the knowledge base."

    results = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "Unknown source")
        content = doc.page_content.strip()
        results.append(f"Source: {source}\nContent: {content}")

    return "\n\n---\n\n".join(results)


# =========================================================
# 9. TOOL REGISTRATION
# =========================================================
tools = [get_stock_price, calculator, brave_search, rag_search]

llm_with_tools = llm.bind_tools(tools)


# =========================================================
# 10. STATE DEFINITION
# =========================================================
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# =========================================================
# 11. CHAT NODE
# =========================================================

def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]

    system_message = SystemMessage(
        content=(
            "You are a helpful assistant. "
            "When the user asks about uploaded files, documents, PDFs, notes, or the knowledge base, "
            "always use the rag_search tool first. "
            "Base your answer only on the retrieved content when using rag_search. "
            "always provide source and all the page numbers"
            "If the retrieved content is insufficient, say so clearly. "
            "Use brave_search only for live web information. "
            "Use calculator only for arithmetic. "
            "Use get_stock_price only for stock price requests."
        )
    )

    response = llm_with_tools.invoke([system_message] + messages)
    return {"messages": [response]}


tool_node = ToolNode(tools)


# =========================================================
# 12. DATABASE AND CHECKPOINTER SETUP
# =========================================================
conn = sqlite3.connect(database=DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)


# =========================================================
# 13. GRAPH CONSTRUCTION
# =========================================================
graph = StateGraph(ChatState)

# nodes
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)

# edges
graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", tools_condition)
graph.add_edge("tools", "chat")

# compile
chat_bot = graph.compile(checkpointer=checkpointer)


# =========================================================
# 14. THREAD MANAGEMENT FUNCTIONS
# =========================================================
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])

    return list(all_threads)


def delete_thread(thread_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    conn.commit()