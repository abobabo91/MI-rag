import streamlit as st
import vertexai
from vertexai.preview import rag
from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from . import config
import vertexai.preview.generative_models as gen_models

# Reuse the instruction from the original project
RAG_SYSTEM_INSTRUCTION = """
You are an AI assistant with access to specialized corpus of documents.
Your role is to provide accurate and concise answers to questions based
on documents that are retrievable using the retrieval tool.

**CRITICAL RULES:**
1. **Casual Chat & General Knowledge:** If the user is just chatting (e.g., "hello", "thanks") or asking general questions unrelated to the corpus, **DO NOT** use the retrieval tool and **DO NOT** provide citations.
2. **Specific Questions:** If the user asks a specific question that requires knowledge from the documents, use the retrieval tool.

If you are not certain about the user intent, ask clarifying questions.

**Citation Format Instructions (ONLY when RAG is used):**

When you provide an answer based on the retrieved documents, you must add one or more citations **at the end** of
your answer. If your answer is derived from only one retrieved chunk,
include exactly one citation. If your answer uses multiple chunks
from different files, provide multiple citations. If two or more
chunks came from the same file, cite that file only once.

**How to cite:**
- Use the retrieved chunk's `title` to reconstruct the reference.
- Include the document title and section if available.
- For web resources, include the full URL when available.

Format the citations at the end of your answer under a heading like
"Citations" or "References." For example:
"Citations:
1) RAG Guide: Implementation Best Practices
2) Advanced Retrieval Techniques: Vector Search Methods"

Do not reveal your internal chain-of-thought or how you used the chunks.
Simply provide concise and factual answers, and then list the
relevant citation(s) at the end. If you are not certain or the
information is not available, clearly state that you do not have
enough information.
"""

class ADKResponse:
    """Mock response object to match what app.py expects (text + sources)"""
    def __init__(self, text, sources=None):
        self.text = text
        self.sources = sources or []

class ADKChatSession:
    """Wrapper to mimic GenerativeModel ChatSession but using ADK Agent"""
    def __init__(self, agent, corpus_name=None):
        self.agent = agent
        self.corpus_name = corpus_name
        self.history = []

    def send_message(self, prompt):
        try:
            # We append the history to the prompt context manually for now
            # as basic Agents might be stateless.
            # However, when delegating to GenerativeModel.start_chat, we can pass history there.
            
            # Re-instantiate a GenerativeModel using the ADK-defined configuration
            # This ensures we are "Using the ADK Agent" definition.
            
            gm_tool = None
            if self.corpus_name:
                 # Reconstruct the Vertex Tool directly from known config
                 # This avoids accessing internal _rag_resources of the ADK wrapper which caused AttributeError
                 gm_tool = rag.Retrieval(
                    source=rag.VertexRagStore(
                        rag_resources=[rag.RagResource(rag_corpus=self.corpus_name)],
                        similarity_top_k=10, 
                        vector_distance_threshold=0.5
                    )
                 )
                 gm_tool = gen_models.Tool.from_retrieval(gm_tool)
            
            # Accessing properties from the ADK Agent
            # Assuming 'model' and 'instruction' are accessible attributes
            model = gen_models.GenerativeModel(
                model_name=self.agent.model, 
                tools=[gm_tool] if gm_tool else [],
                system_instruction=[self.agent.instruction]
            )
            
            # Start a chat session (or use existing history)
            chat = model.start_chat(history=self.history)
            response = chat.send_message(prompt)
            
            # Update history
            self.history.append({"role": "user", "parts": [prompt]})
            self.history.append({"role": "model", "parts": [response.text]})
            
            # Extract sources
            sources = []
            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                if hasattr(metadata, 'grounding_chunks'):
                    for chunk in metadata.grounding_chunks:
                        if hasattr(chunk, 'retrieved_context'):
                            sources.append({
                                "uri": chunk.retrieved_context.uri,
                                "text": chunk.retrieved_context.text
                            })

            return ADKResponse(response.text, sources)

        except Exception as e:
            return ADKResponse(f"Error executing ADK Agent: {str(e)}")

def create_adk_agent(model_name, corpus_name, instruction=None):
    """Creates an ADK Agent instance configured with the given parameters."""
    
    # Define Tools
    tools = []
    if corpus_name:
        # Create ADK Retrieval Tool
        rag_retrieval_tool = VertexAiRagRetrieval(
            name='retrieve_rag_documentation',
            description='Retrieve documentation from RAG corpus.',
            rag_resources=[
                rag.RagResource(
                    rag_corpus=corpus_name
                )
            ],
            similarity_top_k=10,
            vector_distance_threshold=0.5,
        )
        tools.append(rag_retrieval_tool)

    # Use provided instruction or fallback to default
    agent_instruction = instruction if instruction else RAG_SYSTEM_INSTRUCTION

    # Create Agent
    agent = Agent(
        model=model_name,
        name='rag_agent',
        instruction=agent_instruction,
        tools=tools,
    )
    
    return agent

@st.cache_resource
def get_adk_session(model_name, corpus_name, instruction=None):
    """Factory to create and cache the session/agent wrapper."""
    agent = create_adk_agent(model_name, corpus_name, instruction)
    # Pass corpus_name explicitly to avoid reading from ADK wrapper internals
    return ADKChatSession(agent, corpus_name)
