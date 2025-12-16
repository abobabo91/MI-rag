import streamlit as st
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
import os
import json
from . import config

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

def load_credentials():
    if os.path.exists(config.TOKEN_FILE):
        try:
            with open(config.TOKEN_FILE, "r") as f:
                data = json.load(f)
                return google.oauth2.credentials.Credentials.from_authorized_user_info(data)
        except Exception as e:
            st.error(f"Error loading credentials: {e}")
            return None
    return None

def save_credentials(creds):
    try:
        with open(config.TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    except Exception as e:
        st.error(f"Error saving credentials: {e}")

def logout():
    if os.path.exists(config.TOKEN_FILE):
        os.remove(config.TOKEN_FILE)
    if "credentials" in st.session_state:
        del st.session_state.credentials

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
        scopes=config.GOOGLE_AUTH_SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow

def perform_auth():
    """Handles the OAuth flow."""
    # 1. Check if already authenticated in session or token file
    if "credentials" not in st.session_state:
        loaded_creds = load_credentials()
        if loaded_creds:
            st.session_state.credentials = loaded_creds

    if "credentials" in st.session_state:
        creds = st.session_state.credentials
        if creds.valid:
            return True
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(creds)
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
            save_credentials(creds)
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
