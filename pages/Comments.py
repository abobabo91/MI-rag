import streamlit as st
import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core as utils

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="Comments & Wishlist", page_icon="💬", layout="wide")

# -------------------------------
# Authentication & Init
# -------------------------------
if not utils.perform_auth():
    utils.login_page()
    st.stop()

utils.show_sidebar_auth()

st.title("💬 Community Wishlist & Comments")

# -------------------------------
# Community Wishlist
# -------------------------------
todos = utils.load_todos()

# Display Lists (Grid)
if todos:
    keys = list(todos.keys())
    # Iterate in chunks of 3 for grid layout
    for i in range(0, len(keys), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(keys):
                list_name = keys[i+j]
                with cols[j]:
                    st.subheader(list_name)
                    
                    current_content = todos[list_name]
                    display_content = current_content
                    
                    # Handle migration from list to string
                    if isinstance(current_content, list):
                        display_content = "\n".join(current_content)
                    
                    new_content = st.text_area(
                        f"Content for {list_name}", 
                        value=display_content, 
                        key=f"txt_{list_name}", 
                        height=300, # Increased height
                        label_visibility="collapsed"
                    )
                    
                    if new_content != display_content:
                        todos[list_name] = new_content
                        utils.save_todos(todos)

st.markdown("---")

# Management Section (Bottom)
st.subheader("Manage Lists")

c_create, c_delete = st.columns(2)

with c_create:
    st.write("**Create New List**")
    cc1, cc2 = st.columns([0.7, 0.3])
    new_list_name = cc1.text_input("New List Name", label_visibility="collapsed", placeholder="Enter list name")
    if cc2.button("Create List"):
        if new_list_name:
            if new_list_name not in todos:
                todos[new_list_name] = ""
                utils.save_todos(todos)
                st.success(f"Created: {new_list_name}")
                st.rerun()
            else:
                st.error("List exists")
        else:
            st.warning("Enter a name")

with c_delete:
    st.write("**Delete List**")
    if todos:
        cd1, cd2 = st.columns([0.7, 0.3])
        list_to_delete = cd1.selectbox("Select list to delete", options=["Select..."] + list(todos.keys()), label_visibility="collapsed")
        if cd2.button("Delete List"):
            if list_to_delete and list_to_delete != "Select...":
                del todos[list_to_delete]
                utils.save_todos(todos)
                st.success(f"Deleted: {list_to_delete}")
                st.rerun()
            else:
                st.warning("Select a list")
    else:
        st.info("No lists to delete")
