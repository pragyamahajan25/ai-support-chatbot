import faiss
import pickle
import numpy as np
import requests
from pathlib import Path

# Set file paths for FAISS index and metadata
BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "tickets.index"        # FAISS index file
META_PATH = BASE_DIR / "tickets_meta.pkl"      # Pickled ticket metadata

# Embedding API settings
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

# Load FAISS index and ticket metadata
index = faiss.read_index(str(INDEX_PATH))
metadata = pickle.load(open(META_PATH, "rb"))

# Function to get embedding vector for a text using Ollama
def embed(text: str) -> np.ndarray:
    """
    Send the text to Ollama API to get an embedding
    Normalize it so cosine similarity can be used for FAISS search
    """
    r = requests.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    r.raise_for_status()
    emb = np.array(r.json()["embedding"], dtype="float32")
    
    # Check embedding size
    if emb.shape[0] != 768:
        raise ValueError("Unexpected embedding size")
    
    # Normalize for cosine similarity
    faiss.normalize_L2(emb.reshape(1, -1))
    return emb

# Function to retrieve top-k similar tickets for a query
def retrieve_candidates(query: str, top_k: int = 5):
    """
    Convert user query to vector
    Search FAISS index for top-k most similar tickets
    Return ticket metadata and vector similarity score
    """
    q_emb = embed(query).reshape(1, -1)
    scores, indices = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        results.append({
            "ticket": metadata[idx],
            "vector_score": float(score)  # cosine similarity score
        })

    return results
