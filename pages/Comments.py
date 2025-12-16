import streamlit as st
import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core as utils

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="Comments & Wishlist", page_icon="💬", layout="wide", initial_sidebar_state="collapsed")

# -------------------------------
# Authentication & Init
# -------------------------------
if not utils.perform_auth():
    utils.login_page()
    st.stop()

st.title("💬 Community Wishlist & Comments")

# -------------------------------
# Community Wishlist
# -------------------------------
todos = utils.load_todos()

# Create new list
with st.expander("Create New List"):
    new_list_name = st.text_input("List Name")
    if st.button("Create List"):
        if new_list_name and new_list_name not in todos:
            todos[new_list_name] = []
            utils.save_todos(todos)
            st.success(f"Created list: {new_list_name}")
            st.rerun()
        elif new_list_name in todos:
            st.error("List already exists")

# Select and View/Edit List
if todos:
    selected_list = st.selectbox("Select List", list(todos.keys()))
    
    if selected_list:
        st.subheader(f"{selected_list}")
        
        # Add item
        c_input, c_add = st.columns([0.8, 0.2])
        new_item = c_input.text_input("Add Item/Comment", key=f"input_{selected_list}", label_visibility="collapsed", placeholder="Add item...")
        if c_add.button("Add", key=f"btn_{selected_list}"):
            if new_item:
                todos[selected_list].append(new_item)
                utils.save_todos(todos)
                st.rerun()
        
        # Display items
        if todos[selected_list]:
            for item in todos[selected_list]:
                st.text(f"• {item}")
        else:
            st.info("No items yet.")
