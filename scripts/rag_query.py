import sys
import os

# Add parent directory to path to allow importing core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import core.config as config
import vertexai
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

# -------------------------------
# Your RAG engine identifiers
# -------------------------------
PROJECT_ID = config.PROJECT_ID
LOCATION = config.LOCATION
RAG_CORPUS_ID = config.DEFAULT_RAG_CORPUS_ID
RAG_RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{RAG_CORPUS_ID}"

# -------------------------------
# Initialize Vertex AI
# -------------------------------
print(f"Initializing Vertex AI for project {PROJECT_ID}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# -------------------------------
# Define your question
# -------------------------------
user_query = "What are the main topics covered in the documents?"

# -------------------------------
# Create RAG Tool
# -------------------------------
print("Configuring RAG tool...")
retrieval_tool = Tool.from_retrieval(
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

# -------------------------------
# Load Model
# -------------------------------
# Using Gemini 2.5 Flash
model = GenerativeModel("gemini-2.5-flash")

# -------------------------------
# Generate Answer
# -------------------------------
print(f"\nQuestion: {user_query}")
print("Querying RAG engine and generating answer (this may take a moment)...")

try:
    response = model.generate_content(
        user_query,
        tools=[retrieval_tool],
    )

    # -------------------------------
    # Display the results
    # -------------------------------
    print("\n============================")
    print("🧠 LLM Answer:")
    print("============================\n")
    print(response.text)

    print("\n============================")
    print("📄 Retrieved Contexts (Metadata):")
    print("============================\n")
    # Attempt to show grounding metadata if available
    try:
        if response.candidates and response.candidates[0].grounding_metadata:
             print(response.candidates[0].grounding_metadata)
        else:
             print("No grounding metadata returned.")
    except Exception as e:
        print(f"Could not parse grounding metadata: {e}")

except Exception as e:
    print(f"\nError during generation: {e}")
    print("\nPlease ensure you have authenticated with:")
    print("  gcloud auth login")
    print(f"  gcloud config set project {PROJECT_ID}")
    print("  gcloud auth application-default login")
