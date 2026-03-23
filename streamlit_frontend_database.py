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
# 2. UTILITY FUNCTIONS
# =========================================================

# Generate a unique thread ID
def generate_thread_id():
    return f"thread_{uuid.uuid4().hex[:8]}"


# Add a thread if it does not already exist
def add_thread(thread_id):
    if thread_id not in st.session_state["chat_thread"]:
        st.session_state["chat_thread"].append(thread_id)


# Create a new chat
def new_chat():
    new_thread_id = generate_thread_id()
    st.session_state["thread_id"] = new_thread_id
    add_thread(new_thread_id)
    st.session_state["message_history"] = []
    st.session_state["thread_titles"][new_thread_id] = "New Chat"


# Load saved conversation from LangGraph state
def load_conversation(thread_id):
    state = chat_bot.get_state(config={"configurable": {"thread_id": thread_id}})

    if not state or not state.values:
        return []

    return state.values.get("messages", [])


# Generate chat title from first user message
def generate_title_from_messages(thread_id):
    messages = load_conversation(thread_id)

    for msg in messages:
        if isinstance(msg, HumanMessage):
            return msg.content[:40]

    return "New Chat"


# Convert LangGraph messages into UI-friendly message history
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
# 3. USER INPUT
# =========================================================
user_input = st.chat_input("Ask me anything!")


# =========================================================
# 4. SESSION STATE SETUP
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
# 5. RESTORE TITLES AND ACTIVE CHAT HISTORY
# =========================================================
for thread_id in st.session_state["chat_thread"]:
    if thread_id not in st.session_state["thread_titles"]:
        st.session_state["thread_titles"][thread_id] = generate_title_from_messages(thread_id)

if not st.session_state["message_history"] and st.session_state["thread_id"]:
    messages = load_conversation(st.session_state["thread_id"])
    st.session_state["message_history"] = build_message_history(messages)


# =========================================================
# 6. SIDEBAR
# =========================================================
st.sidebar.title("ThreadMind")

st.sidebar.markdown(
    "<div style='margin-top:-10px; margin-bottom:10px; font-size:13px; font-style:italic; color:#888;'>"
    "A multi-thread RAG based conversational AI built with LangGraph, SQLite, FAISS and Streamlit Frontend by Junaeid Shoaib"
    "</div>",
    unsafe_allow_html=True
)

if st.sidebar.button("New Chat"):
    new_chat()

st.sidebar.header("Your Chats")


# =========================================================
# 7. THREAD LIST
# =========================================================
for thread_id in st.session_state["chat_thread"]:
    col1, col2 = st.sidebar.columns([4, 1])

    with col1:
        title = st.session_state["thread_titles"].get(thread_id, thread_id)

        if st.button(title, key=f"open_{thread_id}"):
            st.session_state["thread_id"] = thread_id
            messages = load_conversation(thread_id)
            st.session_state["message_history"] = build_message_history(messages)

    with col2:
        if st.button("✖", key=f"delete_{thread_id}"):
            st.session_state["confirm_delete"] = thread_id


# =========================================================
# 8. DELETE CONFIRMATION
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
# 9. KNOWLEDGE BASE / FILE UPLOAD UI
# =========================================================
st.sidebar.header("Knowledge Base")

uploaded_files = st.sidebar.file_uploader(
    "Upload documents",
    accept_multiple_files=True,
    type=None
)

if st.sidebar.button("Add Files to Knowledge Base"):
    if uploaded_files:
        for uploaded_file in uploaded_files:
            save_uploaded_file(uploaded_file)
        st.sidebar.success("Files added to knowledge base.")
        st.rerun()
    else:
        st.sidebar.warning("Please choose at least one file.")

existing_files = list_uploaded_files()

if existing_files:
    st.sidebar.subheader("Uploaded Files")

    for filename in existing_files:
        file_col1, file_col2 = st.sidebar.columns([4, 1])

        with file_col1:
            st.write(filename)

        with file_col2:
            if st.button("✖", key=f"delete_file_{filename}"):
                delete_uploaded_file(filename)
                st.rerun()

    if st.sidebar.button("Clear Knowledge Base"):
        clear_knowledge_base()
        st.sidebar.success("Knowledge base cleared.")
        st.rerun()
else:
    st.sidebar.caption("No files uploaded yet.")


# =========================================================
# 10. LANGGRAPH CONFIG
# =========================================================
CONFIG = {
    "configurable": {"thread_id": st.session_state["thread_id"]},
    "metadata": {
        "thread_id": st.session_state["thread_id"]
    },
    "run_name": "chat_turn",
}


# =========================================================
# 11. DISPLAY CHAT HISTORY
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
# 12. HANDLE NEW USER MESSAGE
# =========================================================
if user_input:
    current_thread_id = st.session_state["thread_id"]

    # Rename default thread title using first user message
    if st.session_state["thread_titles"].get(current_thread_id) == "New Chat":
        st.session_state["thread_titles"][current_thread_id] = user_input[:40]

    # Save and show user message
    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Get message count before invoke
    before_state = chat_bot.get_state(config=CONFIG)
    before_messages = before_state.values.get("messages", []) if before_state and before_state.values else []

    # Show assistant area with live status
    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=True) as status:
            status.write("Understanding your request...")

            # Run graph
            chat_bot.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG
            )

            status.write("Checking tool usage...")

            # Get only new messages from this turn
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

        st.markdown(final_response)

    # Save assistant response
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": final_response
    })