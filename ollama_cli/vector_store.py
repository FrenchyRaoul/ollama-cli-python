import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import requests


class VectorStore:
    """Manage vector embeddings and semantic search using Qdrant."""
    
    def __init__(self, qdrant_host: str, qdrant_port: int, ollama_base_url: str, embedding_model: str = "nomic-embed-text"):
        """Initialize vector store.
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            ollama_base_url: Ollama API base URL for embeddings
            embedding_model: Model to use for embeddings
        """
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.ollama_base_url = ollama_base_url
        self.collection_name = "ollama_conversations"
        self.embedding_model = embedding_model
        
        # Initialize collection if it doesn't exist
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Get embedding dimension by creating a test embedding
                test_embedding = self._get_embedding("test")
                vector_size = len(test_embedding)
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
        except Exception as e:
            # If Qdrant is not available, we'll handle it gracefully
            pass
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector from Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        url = f"{self.ollama_base_url}/api/embeddings"
        payload = {
            "model": self.embedding_model,
            "prompt": text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            raise RuntimeError(f"Failed to get embedding: {e}")
    
    def add_conversation(self, question: str, answer: str, metadata: Optional[Dict] = None):
        """Add a conversation to the vector store.
        
        Args:
            question: User's question
            answer: Model's answer
            metadata: Additional metadata (model, timestamp, etc.)
        """
        try:
            # Combine question and answer for embedding
            text = f"Question: {question}\nAnswer: {answer}"
            embedding = self._get_embedding(text)
            
            # Prepare metadata
            payload = {
                "question": question,
                "answer": answer,
                **(metadata or {})
            }
            
            # Add to Qdrant
            point_id = str(uuid.uuid4())
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
        except Exception:
            # Silently fail if vector store is unavailable
            pass
    
    def search_similar(self, query: str, limit: int = 3) -> List[Dict]:
        """Search for similar conversations.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of similar conversations with metadata
        """
        try:
            query_embedding = self._get_embedding(query)
            
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            return [
                {
                    "question": hit.payload.get("question", ""),
                    "answer": hit.payload.get("answer", ""),
                    "score": hit.score,
                    **{k: v for k, v in hit.payload.items() if k not in ["question", "answer"]}
                }
                for hit in results
            ]
        except Exception:
            # Return empty list if search fails
            return []
    
    def get_context_from_search(self, query: str, limit: int = 3, min_score: float = 0.7) -> str:
        """Get formatted context from similar conversations.
        
        Args:
            query: Search query
            limit: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            Formatted context string
        """
        results = self.search_similar(query, limit)
        
        if not results:
            return ""
        
        # Filter by minimum score
        relevant = [r for r in results if r["score"] >= min_score]
        
        if not relevant:
            return ""
        
        context_parts = ["Relevant previous conversations:"]
        for i, result in enumerate(relevant, 1):
            context_parts.append(f"\n{i}. Q: {result['question']}")
            context_parts.append(f"   A: {result['answer'][:200]}{'...' if len(result['answer']) > 200 else ''}")
        
        return "\n".join(context_parts)

# Made with Bob
