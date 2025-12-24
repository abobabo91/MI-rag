import os

PROJECT_ID = "isd-1-440812"
LOCATION = "us-east1"
# RAG_CORPUS_ID might be overwritten by session state
DEFAULT_RAG_CORPUS_ID = "6917529027641081856" 

GOOGLE_AUTH_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
TODO_FILE = "todo_lists.json"
RAG_ENGINES_FILE = "rag_engines.json"
TOKEN_FILE = "token.json"
SYSTEM_INSTRUCTION_FILE = "system_instruction.txt"
SYSTEM_INSTRUCTIONS_DB = "system_instructions.json"
