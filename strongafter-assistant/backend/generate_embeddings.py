import os
import json
import numpy as np
from typing import List, Dict, Tuple
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


from utils.embeddings import EmbeddingStore
from utils.file_processor import process_all_markdown_files
from models.excerpt import Excerpt


def save_index(index_path: str, texts: List[str], embeddings: List[List[float]]):
    """Save the index data to disk."""
    data = {
        'texts': texts,
        'embeddings': embeddings
    }
    with open(index_path, 'w') as f:
        json.dump(data, f)


def load_index(index_path: str) -> Dict:
    """Load the index data from disk."""
    with open(index_path, 'r') as f:
        return json.load(f)


def process_texts(texts: List[str]) -> List[List[float]]:
    """Process texts one at a time to avoid API limits."""
    all_embeddings = []
    embedding_store = EmbeddingStore()
    
    for i, text in enumerate(texts):
        print(f"Processing text {i + 1}/{len(texts)}")
        try:
            embedding = embedding_store.get_embedding(text)
            all_embeddings.append(embedding)
        except Exception as e:
            print(f"Error processing text {i + 1}: {e}")
            raise
    
    return all_embeddings


def load_themes(themes_path: str) -> List[Dict]:
    """Load themes from JSON file."""
    with open(themes_path, 'r') as f:
        return json.load(f)


def find_similar_excerpts(theme_text: str, excerpt_texts: List[str], embedding_store: EmbeddingStore, top_k: int = 30) -> List[Tuple[str, float]]:
    """Find the most similar excerpts for a given theme text."""
    # Get embedding for the theme text
    theme_embedding = embedding_store.get_embedding(theme_text)
    
    # Convert to numpy array and reshape for FAISS
    theme_embedding_array = np.array([theme_embedding]).astype('float32')
    
    # Get similar texts using FAISS
    distances: list[list[float]]
    indices: list[list[int]]
    distances, indices = embedding_store.index.search(theme_embedding_array, top_k)
    
    # Convert distances to similarity scores (1 - normalized distance)
    # Use a very low threshold for debugging
    similarity_scores = [1 - (d / 100) for d in distances[0]]  # Using 100 as denominator to make scores higher
    
    # Get the actual texts using the indices
    similar_texts = []
    for idx, score in zip(indices[0], similarity_scores):
        text = excerpt_texts[idx]
        similar_texts.append((text, score))
    
    return similar_texts


def save_retrievals(retrievals: Dict, output_path: str):
    """Save the retrievals to a JSON file."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert Excerpt objects to dictionaries
    serializable_retrievals = {}
    for theme_label, theme_data in retrievals.items():
        serializable_retrievals[theme_label] = {
            'label': theme_data['label'],
            'description': theme_data['description'],
            'similar_excerpts': [
                {
                    'excerpt': {
                        k: v for k, v in excerpt_dict.items() 
                        if k != 'embedding'  # Exclude the embedding field
                    },
                    'similarity_score': score
                }
                for excerpt_dict, score in theme_data['similar_excerpts']
            ]
        }
    
    with open(output_path, 'w') as f:
        json.dump(serializable_retrievals, f, indent=2)


def main():
    # Process all markdown files
    books_dir = os.path.join(os.path.dirname(__file__), 'resources', 'books')
    print(f"Processing books from: {books_dir}")
    
    # Get all excerpts
    excerpts = process_all_markdown_files(books_dir)
    print(f"Found {len(excerpts)} excerpts")
    
    # Extract texts from excerpts
    excerpt_texts = [excerpt.text for excerpt in excerpts]
    
    # Load themes
    themes_path = os.path.join(os.path.dirname(__file__), 'resources', 'strongAfter_themes.json')
    print(f"Loading themes from: {themes_path}")
    themes = load_themes(themes_path)
    
    # Generate embeddings for excerpts only
    print("Generating embeddings...")
    embeddings = process_texts(excerpt_texts)
    
    # Create FAISS index with only excerpts
    print("Creating FAISS index...")
    embedding_store = EmbeddingStore()
    embedding_store.create_index(excerpt_texts, embeddings)
    
    # Save the index data
    index_path = os.path.join(os.path.dirname(__file__), 'resources', 'embeddings_index.json')
    print(f"Saving index to: {index_path}")
    save_index(index_path, excerpt_texts, embeddings)
    
    # Find similar excerpts for each theme
    print("Finding similar excerpts for each theme...")
    retrievals = {}
    for theme in themes:
        print(f"Processing theme: {theme['label']}")
        # Find similar excerpts for both theme label and description
        label_similar = find_similar_excerpts(f"Theme: {theme['label']}", excerpt_texts, embedding_store)
        desc_similar = find_similar_excerpts(f"Description: {theme['description']}", excerpt_texts, embedding_store)
        
        # Combine and sort by similarity score
        all_similar = label_similar + desc_similar
        all_similar.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 15 unique excerpts
        seen_texts = set()
        unique_similar = []
        for text, score in all_similar:
            if text not in seen_texts:
                seen_texts.add(text)
                # Find the original excerpt object for this text
                original_excerpt = next((excerpt for excerpt in excerpts if excerpt.text == text), None)
                if original_excerpt:
                    unique_similar.append((original_excerpt.to_dict(), score))
                if len(unique_similar) >= 15:  # Changed from 5 to 15
                    break
        
        retrievals[theme['label']] = {
            'label': theme['label'],
            'description': theme['description'],
            'similar_excerpts': unique_similar
        }
    
    # Save retrievals
    retrievals_path = os.path.join(os.path.dirname(__file__), 'resources', 'generated', 'retrievals.json')
    print(f"Saving retrievals to: {retrievals_path}")
    save_retrievals(retrievals, retrievals_path)
    
    print("Done!")


if __name__ == '__main__':
    main() 