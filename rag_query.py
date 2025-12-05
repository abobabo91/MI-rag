import vertexai
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

# -------------------------------
# Your RAG engine identifiers
# -------------------------------
project_id = "isd-1-440812"
location = "us-east1"
rag_corpus_id = "6917529027641081856"
rag_resource_name = f"projects/{project_id}/locations/{location}/ragCorpora/{rag_corpus_id}"

# -------------------------------
# Initialize Vertex AI
# -------------------------------
print(f"Initializing Vertex AI for project {project_id}...")
vertexai.init(project=project_id, location=location)

# -------------------------------
# Define your question
# -------------------------------
question = "What are the main topics covered in the documents?"

# -------------------------------
# Create RAG Tool
# -------------------------------
print("Configuring RAG tool...")
rag_tool = Tool.from_retrieval(
    retrieval=rag.Retrieval(
        source=rag.VertexRagStore(
            rag_resources=[
                rag.RagResource(
                    rag_corpus=rag_resource_name
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
print(f"\nQuestion: {question}")
print("Querying RAG engine and generating answer (this may take a moment)...")

try:
    response = model.generate_content(
        question,
        tools=[rag_tool],
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
    print(f"  gcloud config set project {project_id}")
    print("  gcloud auth application-default login")
