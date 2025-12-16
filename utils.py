import streamlit as st
import vertexai
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool
import os
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request

# -------------------------------
# Configuration
# -------------------------------
PROJECT_ID = "isd-1-440812"
LOCATION = "us-east1"
# RAG_CORPUS_ID might be overwritten by session state
DEFAULT_RAG_CORPUS_ID = "6917529027641081856" 

GOOGLE_AUTH_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
TODO_FILE = "todo_lists.json"
RAG_ENGINES_FILE = "rag_engines.json"

def get_redirect_uri():
    try:
        secrets_loaded = "google_auth" in st.secrets
    except FileNotFoundError:
        secrets_loaded = False

    if secrets_loaded:
        auth_secrets = st.secrets["google_auth"]
        if "redirect_uri" in auth_secrets:
            return auth_secrets["redirect_uri"]
        elif "redirect_uris" in auth_secrets:
            uris = auth_secrets["redirect_uris"]
            if isinstance(uris, list) and len(uris) > 0:
                return uris[0]
            else:
                return uris
    return os.environ.get("REDIRECT_URI", "http://localhost:8501")

REDIRECT_URI = get_redirect_uri()

# -------------------------------
# Todo List Functions
# -------------------------------
def load_todos():
    if not os.path.exists(TODO_FILE):
        return {}
    try:
        with open(TODO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_todos(todos):
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=4)

# -------------------------------
# RAG Engine Functions
# -------------------------------
def load_rag_engines():
    if not os.path.exists(RAG_ENGINES_FILE):
        # Return default if file missing
        return [{"name": "Default Shared Engine", "corpus_id": DEFAULT_RAG_CORPUS_ID, "owner": "system", "is_default": True}]
    try:
        with open(RAG_ENGINES_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_rag_engines(engines):
    with open(RAG_ENGINES_FILE, "w") as f:
        json.dump(engines, f, indent=4)

# -------------------------------
# Auth Functions
# -------------------------------
def get_flow_from_secrets():
    """Creates an OAuth Flow object from Streamlit secrets or Env Vars."""
    client_config = None
    
    try:
        secrets_loaded = "google_auth" in st.secrets
    except FileNotFoundError:
        secrets_loaded = False

    if secrets_loaded:
        client_config = {
            "web": {
                "client_id": st.secrets["google_auth"]["client_id"],
                "client_secret": st.secrets["google_auth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        }
    elif os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"):
        client_config = {
            "web": {
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        }
    
    if not client_config:
        st.error("Missing Auth Configuration.")
        st.info("Please set secrets.toml or Environment Variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET).")
        st.stop()
        return None
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=GOOGLE_AUTH_SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow

def perform_auth():
    """Handles the OAuth flow."""
    # 1. Check if already authenticated in session
    if "credentials" in st.session_state:
        creds = st.session_state.credentials
        if creds.valid:
            return True
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                return True
            except:
                st.session_state.credentials = None
    
    # 2. Check for auth code in URL (Redirect back from Google)
    if "code" in st.query_params:
        code = st.query_params["code"]
        try:
            flow = get_flow_from_secrets()
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state.credentials = creds
            # Clear query params to clean URL
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Auth error: {e}")
            return False

    return False

def login_page():
    """Displays the login button."""
    st.header("Authentication Required")
    st.write("Please log in with your Google Account to access the RAG Engine.")
    
    flow = get_flow_from_secrets()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.markdown(f'<a href="{auth_url}" target="_self" style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #ff4b4b; text-decoration: none; border-radius: 4px;">Login with Google</a>', unsafe_allow_html=True)

# -------------------------------
# Vertex AI & RAG Functions
# -------------------------------
@st.cache_resource
def init_vertex_ai(_credentials):
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=_credentials)
        return True
    except Exception as e:
        return str(e)

RAG_SYSTEM_INSTRUCTION = """
You are an AI assistant with access to specialized corpus of documents.
Your role is to provide accurate and concise answers to questions based
on documents that are retrievable using the retrieval tool.

**CRITICAL RULES:**
1. **Casual Chat & General Knowledge:** If the user is just chatting (e.g., "hello", "thanks") or asking general questions unrelated to the corpus, **DO NOT** use the retrieval tool and **DO NOT** provide citations.
2. **Specific Questions:** If the user asks a specific question that requires knowledge from the documents, use the retrieval tool.

If you are not certain about the user intent, ask clarifying questions.

**Citation Format Instructions (ONLY when RAG is used):**

When you provide an answer based on the retrieved documents, you must add one or more citations **at the end** of
your answer. If your answer is derived from only one retrieved chunk,
include exactly one citation. If your answer uses multiple chunks
from different files, provide multiple citations. If two or more
chunks came from the same file, cite that file only once.

**How to cite:**
- Use the retrieved chunk's `title` to reconstruct the reference.
- Include the document title and section if available.
- For web resources, include the full URL when available.

Format the citations at the end of your answer under a heading like
"Citations" or "References." For example:
"Citations:
1) RAG Guide: Implementation Best Practices
2) Advanced Retrieval Techniques: Vector Search Methods"

Do not reveal your internal chain-of-thought or how you used the chunks.
Simply provide concise and factual answers, and then list the
relevant citation(s) at the end. If you are not certain or the
information is not available, clearly state that you do not have
enough information.
"""

@st.cache_resource
def get_rag_tool(resource_name):
    rag_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(
                        rag_corpus=resource_name
                    )
                ],
                similarity_top_k=10,
                vector_distance_threshold=0.5,
            ),
        )
    )
    return rag_tool

@st.cache_resource
def get_model(_rag_tool, model_name): 
    return GenerativeModel(
        model_name, 
        tools=[_rag_tool],
        system_instruction=[RAG_SYSTEM_INSTRUCTION]
    )
