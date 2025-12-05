import streamlit as st
import vertexai
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool
import os
import tempfile
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request

# -------------------------------
# Configuration
# -------------------------------
PROJECT_ID = "isd-1-440812"
LOCATION = "us-east1"
RAG_CORPUS_ID = "6917529027641081856"
RAG_RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{RAG_CORPUS_ID}"
# Get redirect URI from secrets if available, otherwise default to localhost
if "google_auth" in st.secrets and "redirect_uri" in st.secrets["google_auth"]:
    REDIRECT_URI = st.secrets["google_auth"]["redirect_uri"]
else:
    REDIRECT_URI = "http://localhost:8501"
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="Vertex AI RAG Chat", page_icon="💬", layout="wide")

st.title("💬 Vertex AI RAG Chat")

# -------------------------------
# Auth Functions
# -------------------------------
def get_flow_from_secrets():
    """Creates an OAuth Flow object from Streamlit secrets."""
    if "google_auth" not in st.secrets:
        st.error("Missing `[google_auth]` in `.streamlit/secrets.toml`.")
        st.info("Please create an OAuth Client ID in GCP, download the JSON, and add it to your secrets file.")
        st.stop()
        return None
    
    client_config = {
        "web": {
            "client_id": st.secrets["google_auth"]["client_id"],
            "client_secret": st.secrets["google_auth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI]
        }
    }
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=SCOPES,
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
    
    if st.button("Login with Google", type="primary"):
        flow = get_flow_from_secrets()
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.link_button("Continue to Google Login", auth_url)

# -------------------------------
# Main App Logic
# -------------------------------
def main_app():
    # Initialize Vertex AI with User Credentials
    creds = st.session_state.credentials
    
    @st.cache_resource
    def init_vertex_ai(_credentials):
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=_credentials)
            return True
        except Exception as e:
            return str(e)

    init_status = init_vertex_ai(creds)
    if init_status is not True:
        st.error(f"Failed to initialize Vertex AI: {init_status}")
        st.stop()
    
    st.markdown(f"Chatting with Corpus: `{RAG_CORPUS_ID}` in `{LOCATION}` using **Gemini 2.5 Flash**")
    st.sidebar.success(f"Logged in")
    if st.sidebar.button("Logout"):
        del st.session_state.credentials
        st.rerun()

    # Chat Controls
    if st.sidebar.button("Clear Chat", type="primary"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

    st.sidebar.divider()

    # -------------------------------
    # Document Management (Sidebar)
    # -------------------------------
    st.sidebar.header("📂 Manage Documents")

    # Upload Document
    uploaded_file = st.sidebar.file_uploader("Upload a new document", type=["txt", "pdf", "docx", "html"])

    if uploaded_file:
        if st.sidebar.button("Process & Upload"):
            with st.sidebar.status("Uploading document...") as status:
                try:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    status.write("Sending to Vertex AI...")
                    
                    # Upload to RAG Corpus
                    rag_file = rag.upload_file(
                        corpus_name=RAG_RESOURCE_NAME,
                        path=tmp_path,
                        display_name=uploaded_file.name
                    )
                    
                    # Clean up
                    os.remove(tmp_path)
                    
                    status.update(label="Upload Complete!", state="complete", expanded=False)
                    st.sidebar.success(f"Uploaded: {uploaded_file.name}")
                    st.rerun() # Refresh list
                    
                except Exception as e:
                    status.update(label="Upload Failed", state="error")
                    st.sidebar.error(f"Error: {e}")

    st.sidebar.divider()

    # List Documents
    if "file_list" not in st.session_state:
        st.session_state.file_list = []

    def refresh_file_list():
        try:
            files = list(rag.list_files(corpus_name=RAG_RESOURCE_NAME))
            st.session_state.file_list = files
        except Exception as e:
            st.sidebar.error(f"Could not list files: {e}")

    # Initial Load
    if not st.session_state.file_list:
        refresh_file_list()

    if st.sidebar.button("Refresh File List"):
        refresh_file_list()

    # Display Files in Sidebar
    if st.session_state.file_list:
        st.sidebar.write(f"**Total Documents:** {len(st.session_state.file_list)}")
        
        with st.sidebar.expander("View / Delete Files"):
            for f in st.session_state.file_list:
                col1, col2 = st.columns([0.8, 0.2])
                col1.text(f.display_name)
                if col2.button("🗑️", key=f.name, help=f"Delete {f.display_name}"):
                    try:
                        rag.delete_file(name=f.name)
                        st.toast(f"Deleted {f.display_name}")
                        refresh_file_list()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete: {e}")

    # -------------------------------
    # RAG Tool Setup
    # -------------------------------
    @st.cache_resource
    def get_rag_tool():
        rag_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(
                source=rag.VertexRagStore(
                    rag_resources=[
                        rag.RagResource(
                            rag_corpus=RAG_RESOURCE_NAME
                        )
                    ],
                    similarity_top_k=5,
                ),
            )
        )
        return rag_tool

    @st.cache_resource
    def get_model(_rag_tool): 
        return GenerativeModel("gemini-2.5-flash", tools=[_rag_tool])

    # -------------------------------
    # Session State Initialization
    # -------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_session" not in st.session_state or st.session_state.chat_session is None:
        # Initialize chat session
        rag_tool = get_rag_tool()
        model = get_model(rag_tool)
        st.session_state.chat_session = model.start_chat()

    # -------------------------------
    # Chat Interface
    # -------------------------------

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display sources if available
            if "sources" in message:
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**URI:** `{source['uri']}`")
                        st.text(source['text'])

    # User Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Send message to Vertex AI Chat Session
                    response = st.session_state.chat_session.send_message(prompt)
                    
                    text_response = response.text
                    
                    # Extract sources
                    sources = []
                    if response.candidates and response.candidates[0].grounding_metadata:
                        metadata = response.candidates[0].grounding_metadata
                        if hasattr(metadata, 'grounding_chunks'):
                            for chunk in metadata.grounding_chunks:
                                if hasattr(chunk, 'retrieved_context'):
                                    sources.append({
                                        "uri": chunk.retrieved_context.uri,
                                        "text": chunk.retrieved_context.text
                                    })
                    
                    st.markdown(text_response)
                    
                    if sources:
                        with st.expander("Sources"):
                            for source in sources:
                                st.markdown(f"**URI:** `{source['uri']}`")
                                st.text(source['text'])
                    
                    # Save assistant response to state
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": text_response,
                        "sources": sources
                    })
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# -------------------------------
# Entry Point
# -------------------------------
if perform_auth():
    main_app()
else:
    login_page()
