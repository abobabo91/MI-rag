import streamlit as st
import core as utils

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="MI RAG Chat", page_icon="💬", layout="wide", initial_sidebar_state="collapsed")

# -------------------------------
# Entry Point & Auth
# -------------------------------
if utils.perform_auth():
    # Initialize Vertex AI with User Credentials
    creds = st.session_state.credentials
    
    init_status = utils.init_vertex_ai(creds)
    if init_status is not True:
        st.error(f"Failed to initialize Vertex AI: {init_status}")
        st.stop()
    
    st.sidebar.success(f"Logged in")
    if st.sidebar.button("Logout"):
        utils.logout()
        st.rerun()
        
    st.sidebar.divider()
    st.sidebar.caption("v2.0 (ADK)")

    st.title("💬 MI RAG Chat")

    # -------------------------------
    # Session Initialization
    # -------------------------------
    # Ensure RAG Engine is selected
    if "current_rag_corpus_id" not in st.session_state:
         engines = utils.load_rag_engines()
         # Find default or take first
         default_engine = next((e for e in engines if e.get("is_default")), engines[0] if engines else None)
         if default_engine:
             st.session_state.current_rag_corpus_id = default_engine["corpus_id"]
         else:
             st.error("No RAG Engine configuration found.")
             st.stop()

    current_corpus_id = st.session_state.current_rag_corpus_id
    current_rag_resource_name = f"projects/{utils.PROJECT_ID}/locations/{utils.LOCATION}/ragCorpora/{current_corpus_id}"
    
    # Ensure Model is selected
    if "current_model_id" not in st.session_state:
        st.session_state.current_model_id = "gemini-2.5-flash"
    
    current_model_id = st.session_state.current_model_id

    st.caption(f"Using **{current_model_id}** with Corpus `{current_corpus_id}`")

    # -------------------------------
    # Chat Logic
    # -------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_session" not in st.session_state or st.session_state.chat_session is None:
        # Load system instruction
        instruction = utils.load_system_instruction()
        # Initialize ADK chat session
        st.session_state.chat_session = utils.get_adk_session(current_model_id, current_rag_resource_name, instruction)

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
                    # Send message to ADK Agent Session
                    response = st.session_state.chat_session.send_message(prompt)
                    
                    text_response = response.text
                    
                    # Extract sources (using ADK wrapper's pre-processed sources)
                    sources = getattr(response, 'sources', [])
                    
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

    # Chat Controls in Sidebar
    if st.sidebar.button("Clear Chat", type="primary"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

else:
    utils.login_page()
