import streamlit as st
from langgraph_backend import chat_bot
from langchain_core.messages import HumanMessage
import uuid

#-----------------------------Uitility Functions ---------------------------------------------

# generating dynamic thread_id
def generate_thread_id():
    return f"thread_{uuid.uuid4().hex[:8]}"

#new chat

def new_chat():
    new_thread_id = generate_thread_id()
    st.session_state['thread_id'] = new_thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)

def load_conversation(thread_id):
    return chat_bot.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']


#input from user
user_input = st.chat_input("Ask me anything!")

#----------------------------- Session setup ---------------------------------------------------

# Initialize message history in session state if it doesn't exist(saving the conversation history in session state)
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = []

add_thread(st.session_state['thread_id'])
#------------------------------- Side Bar UI ----------------------------------------------

st.sidebar.title("LangGraphChat AI")

st.sidebar.markdown(
    "<div style='margin-top:-10px; font-size:13px; font-style:italic; color:#888;'>"
    "by Junaeid Shoaib"
    "</div>",
    unsafe_allow_html=True
)

if st.sidebar.button('New Chat'):
    new_chat()

st.sidebar.header('Your Chats')

for thread_id in st.session_state['chat_thread']:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            else:
                role = "assistant"
            temp_messages.append({'role':role, 'content':msg.content})
        
        st.session_state['message_history'] = temp_messages


#----------------------------- UI Setup --------------------------------------------------------

CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
# Display the chat messages
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process user input and generate assistant response
if user_input:
    
    #first saving
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    #displaying the user message
    with st.chat_message("user"):
        st.markdown(user_input)

  
    #displaying the assistant message
    with st.chat_message("assistant"):
        ai_messages= st.write_stream(
            message_chunk.content for message_chunk, metadata in chat_bot.stream(
                {'messages': [HumanMessage(content=user_input)]}, config=CONFIG, stream_mode="messages"
            )
        )


      #saving
    st.session_state["message_history"].append({"role": "assistant", "content": ai_messages})
