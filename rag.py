# =========================================================
# 1. IMPORTS
# =========================================================
import streamlit as st
from langgraph_backend_database import (
    chat_bot,
    retrieve_all_threads,
    delete_thread,
    save_uploaded_file,
    list_uploaded_files,
    delete_uploaded_file,
    clear_knowledge_base,
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid


# =========================================================
# 2. PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="ThreadMind",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 3. CUSTOM CSS
# =========================================================
st.markdown("""
<style>
    .stApp {
        background-color: #0f1117;
        color: #f3f4f6;
    }

    section[data-testid="stSidebar"] {
        background: #151924;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
    }

    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 1rem;
        max-width: 1050px;
    }

    .app-title {
        font-size: 1.55rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
        color: #ffffff;
    }

    .app-subtitle {
        font-size: 0.86rem;
        color: #9aa4b2;
        line-height: 1.45;
        margin-bottom: 0.85rem;
    }

    .main-header {
        padding: 0.2rem 0 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }

    .main-header-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.1rem;
    }

    .main-header-subtitle {
        font-size: 0.95rem;
        color: #9aa4b2;
    }

    .section-divider {
        margin: 1rem 0 0.8rem 0;
        border-top: 1px solid rgba(255,255,255,0.08);
    }

    .section-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #d6dae1;
        margin-bottom: 0.55rem;
    }

    .muted-text {
        color: #9aa4b2;
        font-size: 0.84rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        background: #1b2230;
        color: #ffffff;
        padding: 0.55rem 0.8rem;
        font-weight: 500;
        transition: 0.2s ease;
    }

    .stButton > button:hover {
        background: #242d3e;
        border-color: rgba(255,255,255,0.18);
    }

    .stButton > button:focus {
        box-shadow: none;
        border-color: rgba(255,255,255,0.18);
    }

    [data-testid="stFileUploader"] {
        border: 1px dashed rgba(255,255,255,0.16);
        border-radius: 12px;
        padding: 0.35rem;
        background: rgba(255,255,255,0.02);
    }

    [data-testid="stChatInput"] {
        border-top: 1px solid rgba(255,255,255,0.08);
        padding-top: 0.75rem;
        margin-top: 0.5rem;
    }

    [data-testid="stChatMessage"] {
        border-radius: 14px;
    }

    .thread-caption {
        color: #9aa4b2;
        font-size: 0.8rem;
        margin-bottom: 0.2rem;
    }

    .file-name {
        font-size: 0.92rem;
        color: #e8eaee;
        padding-top: 0.35rem;
        word-break: break-word;
    }

    .tiny-note {
        color: #8f98a6;
        font-size: 0.78rem;
        margin-top: -0.25rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 4. UTILITY FUNCTIONS
# =========================================================

def generate_thread_id():
    return f"thread_{uuid.uuid4().hex[:8]}"


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_thread"]:
        st.session_state["chat_thread"].append(thread_id)


def new_chat():
    new_thread_id = generate_thread_id()
    st.session_state["thread_id"] = new_thread_id
    add_thread(new_thread_id)
    st.session_state["message_history"] = []
    st.session_state["thread_titles"][new_thread_id] = "New Chat"


def load_conversation(thread_id):
    state = chat_bot.get_state(config={"configurable": {"thread_id": thread_id}})

    if not state or not state.values:
        return []

    return state.values.get("messages", [])


def generate_title_from_messages(thread_id):
    messages = load_conversation(thread_id)

    for msg in messages:
        if isinstance(msg, HumanMessage):
            title = msg.content.strip().replace("\n", " ")
            return title[:35] + "..." if len(title) > 35 else title

    return "New Chat"


def build_message_history(messages):
    temp_messages = []

    for msg in messages:
        if isinstance(msg, HumanMessage):
            temp_messages.append({
                "role": "user",
                "content": msg.content
            })

        elif isinstance(msg, AIMessage):
            if msg.content:
                temp_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })

            if getattr(msg, "tool_calls", None):
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "unknown_tool")
                    temp_messages.append({
                        "role": "tool",
                        "content": f"Using tool: {tool_name}"
                    })

        elif isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", "tool")
            temp_messages.append({
                "role": "tool",
                "content": f"Tool finished: {tool_name}"
            })

    return temp_messages


# =========================================================
# 5. SESSION STATE SETUP
# =========================================================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "chat_thread" not in st.session_state:
    st.session_state["chat_thread"] = retrieve_all_threads()

if "thread_id" not in st.session_state:
    if st.session_state["chat_thread"]:
        st.session_state["thread_id"] = st.session_state["chat_thread"][0]
    else:
        new_thread_id = generate_thread_id()
        st.session_state["thread_id"] = new_thread_id
        st.session_state["chat_thread"] = [new_thread_id]

if "thread_titles" not in st.session_state:
    st.session_state["thread_titles"] = {}

if "confirm_delete" not in st.session_state:
    st.session_state["confirm_delete"] = None

add_thread(st.session_state["thread_id"])


# =========================================================
# 6. RESTORE TITLES AND ACTIVE CHAT HISTORY
# =========================================================
for thread_id in st.session_state["chat_thread"]:
    if thread_id not in st.session_state["thread_titles"]:
        st.session_state["thread_titles"][thread_id] = generate_title_from_messages(thread_id)

if not st.session_state["message_history"] and st.session_state["thread_id"]:
    messages = load_conversation(st.session_state["thread_id"])
    st.session_state["message_history"] = build_message_history(messages)


# =========================================================
# 7. SIDEBAR
# =========================================================
st.sidebar.markdown("""
<div class="app-title">ThreadMind</div>
<div class="app-subtitle">
    Multi-thread RAG conversational assistant built with LangGraph, SQLite, FAISS, and Streamlit
    by Abu Junaeid Shaoib
</div>

""", unsafe_allow_html=True)

if st.sidebar.button("＋ New Chat"):
    new_chat()
    st.rerun()

st.sidebar.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="section-label">Chats</div>', unsafe_allow_html=True)


# =========================================================
# 8. THREAD LIST
# =========================================================
for thread_id in st.session_state["chat_thread"]:
    col1, col2 = st.sidebar.columns([5, 1])

    with col1:
        title = st.session_state["thread_titles"].get(thread_id, thread_id)
        button_label = f"💬 {title}"

        if st.button(button_label, key=f"open_{thread_id}"):
            st.session_state["thread_id"] = thread_id
            messages = load_conversation(thread_id)
            st.session_state["message_history"] = build_message_history(messages)
            st.rerun()

    with col2:
        if st.button("✖", key=f"delete_{thread_id}"):
            st.session_state["confirm_delete"] = thread_id


# =========================================================
# 9. DELETE CONFIRMATION
# =========================================================
if st.session_state["confirm_delete"] is not None:
    pending_thread = st.session_state["confirm_delete"]
    pending_title = st.session_state["thread_titles"].get(pending_thread, pending_thread)

    st.sidebar.warning(f"Delete chat: {pending_title}?")

    confirm_col, cancel_col = st.sidebar.columns(2)

    with confirm_col:
        if st.button("Yes", key=f"confirm_delete_{pending_thread}"):
            delete_thread(pending_thread)

            if pending_thread in st.session_state["chat_thread"]:
                st.session_state["chat_thread"].remove(pending_thread)

            if pending_thread in st.session_state["thread_titles"]:
                del st.session_state["thread_titles"][pending_thread]

            if st.session_state["thread_id"] == pending_thread:
                st.session_state["thread_id"] = generate_thread_id()
                st.session_state["message_history"] = []
                add_thread(st.session_state["thread_id"])
                st.session_state["thread_titles"][st.session_state["thread_id"]] = "New Chat"

            st.session_state["confirm_delete"] = None
            st.rerun()

    with cancel_col:
        if st.button("Cancel", key=f"cancel_delete_{pending_thread}"):
            st.session_state["confirm_delete"] = None
            st.rerun()


# =========================================================
# 10. KNOWLEDGE BASE / FILE UPLOAD UI
# =========================================================
st.sidebar.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="section-label">Knowledge Base</div>', unsafe_allow_html=True)

uploaded_files = st.sidebar.file_uploader(
    "Upload documents",
    accept_multiple_files=True,
    type=None
)

st.sidebar.markdown('<div class="tiny-note">Upload files to make them searchable inside chat.</div>', unsafe_allow_html=True)

if st.sidebar.button("Upload to Knowledge Base"):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            save_uploaded_file(uploaded_file)
        st.sidebar.success("Files added to knowledge base.")
        st.rerun()
    else:
        st.sidebar.warning("Please choose at least one file.")

existing_files = list_uploaded_files()

if existing_files:
    st.sidebar.markdown('<div class="section-label" style="margin-top:0.85rem;">Uploaded Files</div>', unsafe_allow_html=True)

    for filename in existing_files:
        file_col1, file_col2 = st.sidebar.columns([5, 1])

        with file_col1:
            st.markdown(f"<div class='file-name'>📄 {filename}</div>", unsafe_allow_html=True)

        with file_col2:
            if st.button("✖", key=f"delete_file_{filename}"):
                delete_uploaded_file(filename)
                st.rerun()

    if st.sidebar.button("Clear All Files"):
        clear_knowledge_base()
        st.sidebar.success("Knowledge base cleared.")
        st.rerun()
else:
    st.sidebar.caption("No files uploaded yet.")


# =========================================================
# 11. LANGGRAPH CONFIG
# =========================================================
CONFIG = {
    "configurable": {"thread_id": st.session_state["thread_id"]},
    "metadata": {
        "thread_id": st.session_state["thread_id"]
    },
    "run_name": "chat_turn",
}


# =========================================================
# 12. MAIN HEADER
# =========================================================
# st.markdown("""
# <div class="main-header">
#     <div class="main-header-title">ThreadMind</div>
#     <div class="main-header-subtitle">
#         Chat across threads, use tools, and search your uploaded knowledge base
#     </div>
# </div>
# """, unsafe_allow_html=True)


# =========================================================
# 13. DISPLAY CHAT HISTORY
# =========================================================
for message in st.session_state["message_history"]:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])

    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message["content"])

    elif message["role"] == "tool":
        with st.chat_message("assistant"):
            with st.status("Tools", state="complete", expanded=False):
                st.write(message["content"])


# =========================================================
# 14. USER INPUT
# =========================================================
user_input = st.chat_input("Ask me anything...")


# =========================================================
# 15. HANDLE NEW USER MESSAGE
# =========================================================
if user_input:
    current_thread_id = st.session_state["thread_id"]

    if st.session_state["thread_titles"].get(current_thread_id) == "New Chat":
        cleaned_title = user_input.strip().replace("\n", " ")
        st.session_state["thread_titles"][current_thread_id] = (
            cleaned_title[:35] + "..." if len(cleaned_title) > 35 else cleaned_title
        )

    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    before_state = chat_bot.get_state(config=CONFIG)
    before_messages = before_state.values.get("messages", []) if before_state and before_state.values else []

    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=True) as status:
            status.write("Understanding your request...")

            chat_bot.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG
            )

            status.write("Checking tool usage...")

            after_state = chat_bot.get_state(config=CONFIG)
            after_messages = after_state.values.get("messages", []) if after_state and after_state.values else []
            new_messages = after_messages[len(before_messages):]

            final_response = ""

            for msg in new_messages:
                if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get("name", "unknown_tool")
                        status.write(f"Using tool: {tool_name}")

                        st.session_state["message_history"].append({
                            "role": "tool",
                            "content": f"Using tool: {tool_name}"
                        })

                elif isinstance(msg, AIMessage) and msg.content:
                    final_response = msg.content

            status.update(label="Done", state="complete", expanded=False)

        st.markdown(final_response if final_response else "No response generated.")

    st.session_state["message_history"].append({
        "role": "assistant",
        "content": final_response
    })