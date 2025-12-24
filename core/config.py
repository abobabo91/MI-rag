import os

PROJECT_ID = "isd-1-440812"
LOCATION = "us-east1"
# RAG_CORPUS_ID might be overwritten by session state
DEFAULT_RAG_CORPUS_ID = "6917529027641081856" 

GOOGLE_AUTH_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

DATA_DIR = "data"
TODO_FILE = os.path.join(DATA_DIR, "todo_lists.json")
RAG_ENGINES_FILE = os.path.join(DATA_DIR, "rag_engines.json")
TOKEN_FILE = os.path.join(DATA_DIR, "token.json")
SYSTEM_INSTRUCTIONS_DB = os.path.join(DATA_DIR, "system_instructions.json")
