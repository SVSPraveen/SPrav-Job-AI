import os
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from engine.llm_provider import generate

# The SPrav AI Brain
# A RAG memory orchestrator optimized for 8GB VRAM environments.

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "sprav_memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

class SPravBrain:
    def __init__(self):
        # Initialize a persistent ChromaDB client on the SSD to save RAM/VRAM
        self.chroma_client = chromadb.PersistentClient(path=MEMORY_DIR)
        
        # We use nomic-embed-text via Ollama for high-dimensional semantic search.
        # This provides massive retrieval improvements while consuming only ~274MB of memory.
        self.embed_fn = embedding_functions.OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
        
        # Get or create the core memory collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="sprav_core", 
            embedding_function=self.embed_fn
        )
        
        # Text chunker for massive documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def ingest_memory(self, text_content: str, source_id: str, metadata: dict = None):
        """
        Takes a massive document (e.g., application_prompt.md or chat history),
        chunks it into optimal context windows, and dumps it into the Vector DB.
        """
        print(f"[SPrav] Ingesting massive document: {source_id}...")
        chunks = self.text_splitter.split_text(text_content)
        
        ids = [f"{source_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [metadata or {} for _ in range(len(chunks))]
        
        # Add to Vector DB (SSD/RAM, no VRAM used)
        self.collection.upsert(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[SPrav] Successfully stored {len(chunks)} memory chunks in the vector bank.")

    def query(self, user_prompt: str, n_results: int = 3) -> str:
        """
        Retrieves ONLY the relevant text from the Vector DB and builds a targeted prompt 
        for the overarching state machine to answer the user's request.
        """
        print(f"[SPrav] Searching memory for relevant context...")
        results = self.collection.query(
            query_texts=[user_prompt],
            n_results=n_results
        )
        
        retrieved_chunks = results['documents'][0]
        context = "\n\n---\n\n".join(retrieved_chunks)
        
        # Build the targeted prompt
        targeted_prompt = f"""You are the SPrav AI Brain. You have been provided with specific fragments of retrieved memory to answer the user's question.

<retrieved_memory>
{context}
</retrieved_memory>

User Question: {user_prompt}

Please answer the question based solely on the retrieved memory context above.
"""
        print(f"[SPrav] Synthesizing answer using LLM generation...")
        # The generation model (llama3.1:8b) runs in VRAM
        response = generate(targeted_prompt, use_case="brain_retrieval")
        return response
        
    def ingest_kb(self, kb: dict):
        """Indexes the user's Knowledge Base for semantic retrieval.
        
        Bullets are stored nested inside work_history[].bullets and projects[].bullets,
        NOT under a top-level 'resume_bullets' key. This method correctly flattens them.
        """
        kb_collection = self.chroma_client.get_or_create_collection(name="sprav_kb", embedding_function=self.embed_fn)
        
        documents = []
        metadatas = []
        ids = []
        
        # Flatten bullets from work_history entries
        for job in kb.get("work_history", []):
            job_id = job.get("id", "")
            for bullet in job.get("bullets", []):
                text = bullet.get("text", "").strip()
                bid = bullet.get("id", "")
                if text and bid:
                    documents.append(text)
                    metadatas.append({"type": "work_bullet", "parent_id": job_id})
                    ids.append(bid)
        
        # Flatten bullets from project entries
        for project in kb.get("projects", []):
            proj_id = project.get("id", "")
            for bullet in project.get("bullets", []):
                text = bullet.get("text", "").strip()
                bid = bullet.get("id", "")
                if text and bid:
                    documents.append(text)
                    metadatas.append({"type": "project_bullet", "parent_id": proj_id})
                    ids.append(bid)
                    
        if documents:
            print(f"[SPrav Brain] Ingesting {len(documents)} real bullets into vector index.")
            kb_collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        else:
            print("[SPrav Brain] Warning: No bullets found to ingest. Check me.json structure.")

    def query_kb(self, jd_text: str, n_results: int = 20) -> list:
        """Retrieves top relevant KB bullet IDs for a given job description."""
        kb_collection = self.chroma_client.get_or_create_collection(name="sprav_kb", embedding_function=self.embed_fn)
        if kb_collection.count() == 0:
            return []
            
        results = kb_collection.query(
            query_texts=[jd_text],
            n_results=min(n_results, kb_collection.count())
        )
        return results["ids"][0] if results["ids"] else []

# Singleton instance of the brain
brain = SPravBrain()
