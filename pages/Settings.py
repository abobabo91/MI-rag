import streamlit as st
import vertexai
from vertexai.preview import rag
import os
import sys
import tempfile

# Add parent directory to path to allow importing core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core as utils

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")

# -------------------------------
# Authentication & Init
# -------------------------------
if not utils.perform_auth():
    utils.login_page()
    st.stop()

# Initialize Vertex AI
if "credentials" in st.session_state:
    init_status = utils.init_vertex_ai(st.session_state.credentials)
    if init_status is not True:
        st.error(f"Failed to initialize Vertex AI: {init_status}")
        st.stop()

st.title("⚙️ Settings")

# Create tabs for visual separation
tab_rag, tab_model = st.tabs(["📚 RAG Settings", "🤖 Model Settings"])

# -------------------------------
# Tab 1: RAG Settings
# -------------------------------
with tab_rag:
    col_rag_config, col_docs = st.columns([1, 1])

    with col_rag_config:
        # -------------------------------
        # RAG Engine Selection
        # -------------------------------
        st.header("RAG Engine Configuration")
        
        rag_engines = utils.load_rag_engines()

        # Sync with remote engines
        try:
            remote_corpora = utils.list_corpora()
            if remote_corpora:
                remote_map = {c.name.split('/')[-1]: c for c in remote_corpora}
                existing_ids = {e["corpus_id"] for e in rag_engines}
                
                engines_updated = False
                
                # Add found remote engines
                for cid, c in remote_map.items():
                    if cid not in existing_ids:
                        rag_engines.append({
                            "name": c.display_name,
                            "corpus_id": cid,
                            "owner": "user",
                            "is_default": False
                        })
                        engines_updated = True
                
                # Filter out engines that don't exist remotely
                valid_engines = []
                for e in rag_engines:
                    if e["corpus_id"] in remote_map:
                        valid_engines.append(e)
                    else:
                        engines_updated = True # Mark as updated so we save the clean list
                
                if engines_updated:
                    rag_engines = valid_engines
                    utils.save_rag_engines(rag_engines)
                    st.toast("Synced RAG engines with cloud")
                    
        except Exception as e:
            st.warning(f"Could not sync RAG engines: {e}")

        engine_names = [e["name"] for e in rag_engines]
        
        # Default selection logic
        if "selected_engine_index" not in st.session_state:
            st.session_state.selected_engine_index = 0
        
        # Ensure index is valid
        if st.session_state.selected_engine_index >= len(engine_names):
             st.session_state.selected_engine_index = 0

        selected_engine_name = st.selectbox(
            "Select RAG Engine", 
            engine_names, 
            index=st.session_state.selected_engine_index
        )
        
        # Update selected engine
        selected_engine = next((e for e in rag_engines if e["name"] == selected_engine_name), rag_engines[0])
        
        # Update session state index if changed
        st.session_state.selected_engine_index = engine_names.index(selected_engine_name)

        # Store selection in session
        if "current_rag_corpus_id" not in st.session_state or st.session_state.current_rag_corpus_id != selected_engine["corpus_id"]:
            st.session_state.current_rag_corpus_id = selected_engine["corpus_id"]
            # Clear chat and file list when engine changes
            st.session_state.messages = []
            st.session_state.chat_session = None
            st.session_state.file_list = []
            st.rerun()

        current_corpus_id = st.session_state.current_rag_corpus_id
        current_rag_resource_name = f"projects/{utils.PROJECT_ID}/locations/{utils.LOCATION}/ragCorpora/{current_corpus_id}"
        
        st.info(f"Active Corpus ID: `{current_corpus_id}`")

        # Delete Engine
        if not selected_engine.get("is_default", False):
            if st.button("Delete This Engine", type="primary"):
                try:
                    # Attempt to delete from Vertex AI first
                    try:
                        rag.delete_corpus(name=current_rag_resource_name)
                        st.toast(f"Deleted corpus resource: {selected_engine_name}")
                    except Exception as cloud_err:
                        st.warning(f"Cloud resource deletion failed (might contain files): {cloud_err}")
                    
                    # Remove from config
                    new_engines = [e for e in rag_engines if e["name"] != selected_engine_name]
                    utils.save_rag_engines(new_engines)
                    
                    # Reset selection
                    st.session_state.selected_engine_index = 0
                    if new_engines:
                        st.session_state.current_rag_corpus_id = new_engines[0]["corpus_id"]
                    
                    st.success(f"Deleted engine: {selected_engine_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting engine: {e}")

        # Create New Engine
        with st.expander("Create New RAG Engine"):
            new_engine_name = st.text_input("New Engine Name")
            if st.button("Create Engine"):
                if new_engine_name and new_engine_name not in engine_names:
                    try:
                        with st.spinner("Creating new RAG Corpus..."):
                            # Create Corpus
                            corpus = rag.create_corpus(display_name=new_engine_name)
                            new_corpus_id = corpus.name.split("/")[-1]
                            
                            new_engine = {
                                "name": new_engine_name,
                                "corpus_id": new_corpus_id,
                                "owner": "user", 
                                "is_default": False
                            }
                            rag_engines.append(new_engine)
                            utils.save_rag_engines(rag_engines)
                            st.success(f"Created engine: {new_engine_name}")
                            st.session_state.selected_engine_index = len(rag_engines) - 1
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create corpus: {e}")
                elif new_engine_name in engine_names:
                    st.error("Engine with this name already exists")

    with col_docs:
        # -------------------------------
        # Document Management
        # -------------------------------
        st.header("Manage Documents")

        # Upload Document
        uploaded_file = st.file_uploader("Upload a new document", type=["txt", "pdf", "docx", "html"])

        if uploaded_file:
            if st.button("Process & Upload"):
                with st.status("Uploading document...") as status:
                    try:
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name
                        
                        status.write("Sending to Vertex AI...")
                        
                        # Upload to RAG Corpus
                        rag_file = rag.upload_file(
                            corpus_name=current_rag_resource_name,
                            path=tmp_path,
                            display_name=uploaded_file.name
                        )
                        
                        # Clean up
                        os.remove(tmp_path)
                        
                        status.update(label="Upload Complete!", state="complete", expanded=False)
                        st.success(f"Uploaded: {uploaded_file.name}")
                        # Refresh list
                        st.session_state.file_list = [] 
                        st.rerun() 
                        
                    except Exception as e:
                        status.update(label="Upload Failed", state="error")
                        st.error(f"Error: {e}")

        # List Documents
        if "file_list" not in st.session_state:
            st.session_state.file_list = []

        def refresh_file_list():
            try:
                files = list(rag.list_files(corpus_name=current_rag_resource_name))
                st.session_state.file_list = files
            except Exception as e:
                st.error(f"Could not list files: {e}")

        # Initial Load if empty
        if not st.session_state.file_list:
            refresh_file_list()

        col_btn, col_txt = st.columns([0.3, 0.7])
        if col_btn.button("Refresh List"):
            refresh_file_list()
        
        if st.session_state.file_list:
            col_txt.write(f"**Total Documents:** {len(st.session_state.file_list)}")
            
            with st.expander("View / Delete Files", expanded=True):
                for f in st.session_state.file_list:
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.text(f.display_name)
                    if c2.button("🗑️", key=f.name, help=f"Delete {f.display_name}"):
                        try:
                            rag.delete_file(name=f.name)
                            st.toast(f"Deleted {f.display_name}")
                            refresh_file_list()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

# -------------------------------
# Tab 2: Model Settings
# -------------------------------
with tab_model:
    # -------------------------------
    # Model Selection
    # -------------------------------
    st.header("Model Configuration")
    available_models_map = {
        "Gemini 2.5 Flash": "gemini-2.5-flash",
        "Gemini 3 Pro (Preview)": "gemini-3-pro-preview",
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash-Lite": "gemini-2.5-flash-lite",
        "Custom": "custom"
    }
    
    # Determine index for default
    current_model = st.session_state.get("current_model_id", "gemini-2.5-flash")
    # Reverse lookup for UI
    reverse_map = {v: k for k, v in available_models_map.items()}
    default_label = reverse_map.get(current_model, "Custom")
    
    # Simple layout for model selection
    col_model_select, col_model_dummy = st.columns([1, 1])
    
    with col_model_select:
        selected_model_label = st.selectbox("Choose LLM", list(available_models_map.keys()), index=list(available_models_map.keys()).index(default_label) if default_label in available_models_map else 0)
        
        if selected_model_label == "Custom":
            selected_model_id = st.text_input("Enter Model ID", value=current_model if current_model not in available_models_map.values() else "gemini-1.5-pro")
        else:
            selected_model_id = available_models_map[selected_model_label]

        if "current_model_id" not in st.session_state:
            st.session_state.current_model_id = selected_model_id
        
        if st.session_state.current_model_id != selected_model_id:
            st.session_state.current_model_id = selected_model_id
            st.session_state.chat_session = None
            st.toast(f"Model switched to {selected_model_id}")
            st.rerun()
        
        st.info(f"Current Model: `{st.session_state.current_model_id}`")
