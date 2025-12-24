import streamlit as st
import core as utils

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

# -------------------------------
# Entry Point & Auth
# -------------------------------
if utils.perform_auth():
    utils.show_sidebar_auth()
    
    st.title("Welcome to MI RAG Chat")
    st.write("Please select a page from the sidebar to continue.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.subheader("💬 Chat")
            st.write("Interact with your RAG corpus using Gemini.")
            if st.button("Go to Chat"):
                st.switch_page("pages/Chat.py")
                
    with col2:
         with st.container(border=True):
            st.subheader("📝 Comments")
            st.write("View and manage community wishlist.")
            if st.button("Go to Comments"):
                st.switch_page("pages/Comments.py")

    with col3:
         with st.container(border=True):
            st.subheader("⚙️ Settings")
            st.write("Configure RAG engines and models.")
            if st.button("Go to Settings"):
                st.switch_page("pages/Settings.py")

else:
    utils.login_page()
