import os
from typing import List, Dict, Any
import numpy as np
import openai
import faiss

class EmbeddingStore:
    def __init__(self, api_key: str = None):
        """
        Initialize the embedding store.
        
        Args:
            api_key: OpenAI API key (optional, can be set via OPENAI_API_KEY env var)
        """
        openai.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.index = None
        self.texts = []  # Store original texts for retrieval
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=text
        )
        return response['data'][0]['embedding']
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch using OpenAI.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item['embedding'] for item in response['data']]
    
    def create_index(self, texts: List[str], embeddings: List[List[float]] = None):
        """
        Create a FAISS index from texts and their embeddings.
        
        Args:
            texts: List of texts to index
            embeddings: Optional pre-computed embeddings. If None, will compute them.
        """
        if embeddings is None:
            embeddings = self.get_embeddings_batch(texts)
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = len(embeddings[0])
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        # Store original texts
        self.texts = texts
    
    def find_nearest_neighbors(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Find nearest neighbors for a query text.
        
        Args:
            query: Query text
            k: Number of neighbors to return
            
        Returns:
            List of nearest neighbors with their distances
        """
        if not self.index:
            raise ValueError("Index must be created before querying")
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        query_array = np.array([query_embedding]).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_array, k)
        
        # Format results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.texts):  # Ensure index is valid
                results.append({
                    'text': self.texts[idx],
                    'distance': float(distance),
                    'rank': i + 1
                })
        
        return results
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def create_endpoint(self, display_name: str):
        """
        Create a new index endpoint.
        
        Args:
            display_name: Name for the endpoint
        """
        self.endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
            display_name=display_name,
            public_endpoint_enabled=True
        )
    
    def deploy_index(self):
        """
        Deploy the index to the endpoint.
        """
        if not self.index or not self.endpoint:
            raise ValueError("Index and endpoint must be created before deployment")
        
        self.endpoint.deploy_index(
            index=self.index,
            deployed_index_id="deployed_index_1"
        ) 