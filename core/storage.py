import os
import json
from . import config

def load_todos():
    if not os.path.exists(config.TODO_FILE):
        return {}
    try:
        with open(config.TODO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_todos(todos):
    with open(config.TODO_FILE, "w") as f:
        json.dump(todos, f, indent=4)

def load_rag_engines():
    if not os.path.exists(config.RAG_ENGINES_FILE):
        # Return default if file missing
        return [{"name": "Default Shared Engine", "corpus_id": config.DEFAULT_RAG_CORPUS_ID, "owner": "system", "is_default": True}]
    try:
        with open(config.RAG_ENGINES_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_rag_engines(engines):
    with open(config.RAG_ENGINES_FILE, "w") as f:
        json.dump(engines, f, indent=4)
