# ThreadMind

**ThreadMind** is a multi-thread conversational AI chatbot built with **LangGraph** and **Streamlit**.  
It allows users to create multiple conversation threads, switch between them, and continue chats with persistent memory.

The project demonstrates how conversational AI systems can be structured using **graph-based state management**, while providing a simple web interface for interaction.

---

# Overview

ThreadMind was built as a learning and demonstration project to explore:

- conversational AI interfaces
- multi-thread chat systems
- state management using LangGraph
- persistent conversation storage
- building AI applications with Streamlit

The application provides a sidebar where users can:

- create new chats
- switch between chat threads
- delete conversations
- automatically generate chat titles from the first user message

---

# Features

- Multi-thread chat system  
- Persistent conversation state  
- Dynamic chat titles  
- Chat history navigation  
- Chat deletion with confirmation  
- Streaming LLM responses  
- Simple Streamlit user interface  

---

# Two Versions of the Application

This repository contains **two versions** of the chatbot backend.

These are not experiments, but two different ways of handling conversation memory.

---

## 1. In-Memory Version

Files used:
streamlit_frontend.py
langgraph_backend.py


Characteristics:

- conversation state stored in memory
- no database required
- simple and lightweight
- conversation history resets when the application restarts

Best for:

- quick demos
- testing
- understanding LangGraph workflows

Run it using:
streamlit run streamlit_frontend.py

---

## 2. SQLite Database Version (Recommended)

Files used:

---

## 2. SQLite Database Version (Recommended)

Files used:


---

## 2. SQLite Database Version (Recommended)

Files used:

app.py
langgraph_backend_database.py

Characteristics:

- conversation state stored in SQLite
- chat threads persist between sessions
- users can switch between conversations
- closer to a real application setup

This is the **main version intended for deployment**.

Run it using:


Characteristics:

- conversation state stored in SQLite
- chat threads persist between sessions
- users can switch between conversations
- closer to a real application setup

This is the **main version intended for deployment**.

Run it using:
streamlit run app.py

---

# Project Structure
ThreadMind/
│
├── app.py
├── langgraph_backend_database.py
│
├── streamlit_frontend.py
├── langgraph_backend.py
│
├── requirements.txt
├── README.md
├── .gitignore
│
└── .streamlit/
└── secrets.toml (not included in the repository)
---

# Requirements

Python **3.9 or higher** is recommended.

Install dependencies using:

---

# Requirements

Python **3.11 or higher** is recommended.

Install dependencies using:
pip install -r requirements.txt

Main libraries used:

- Streamlit
- LangGraph
- LangChain
- OpenAI
- SQLite
- python-dotenv

---

# API Key Setup

ThreadMind requires an **OpenAI API key**.

Create the following file:

Inside the file add:
.streamlit/secrets.toml

Inside the file add:

Inside the file add:
OPENAI_API_KEY = "your_openai_api_key"

This file should **not be uploaded to GitHub**.

---

# Running the Application

### Run the SQLite Version (recommended)

### Run the In-Memory Version

streamlit run streamlit_frontend.py

---

# How the Chat System Works

ThreadMind uses **LangGraph** to structure the chatbot as a state graph.

The workflow is roughly:

1. User sends a message through the Streamlit interface
2. The message is added to the conversation state
3. LangGraph sends the conversation history to the LLM
4. The model generates a response
5. The response is appended to the conversation state
6. The updated state is saved (either in memory or SQLite)

This approach allows conversations to be handled as **stateful interactions instead of isolated prompts**.

---

# Deployment

ThreadMind can be deployed using **Streamlit Community Cloud**.

Typical steps:

1. Push the repository to GitHub
2. Deploy the repository through Streamlit Cloud
3. Add the OpenAI API key in the **Streamlit secrets manager**
4. Launch the app

---

# Purpose of This Project

This project was built to explore practical aspects of:

- building conversational AI interfaces
- working with LangGraph
- managing chat session state
- designing simple AI applications

It is intended as a **learning and demonstration project**, not a production system.

---

# Possible Improvements

Future enhancements could include:

- authentication
- rate limiting
- better chat title generation
- message editing
- external database support
- conversation export
- usage analytics

---

# License

MIT License

---

# Author

**Abu Junaeid Shoaib**

MSc Artificial Intelligence — University of Essex  
AI / Machine Learning Enthusiast
