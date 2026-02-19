import pandas as pd
import requests
import numpy as np
import faiss
import pickle
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# File paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "tickets_dataset.xlsx"
INDEX_PATH = BASE_DIR / "tickets.index"
META_PATH = BASE_DIR / "tickets_meta.pkl"

# Embedding settings
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
MAX_WORKERS = 8  # Number of threads for parallel embedding
EMBED_DIM = 768

# Embed a single text
def embed(text: str) -> np.ndarray:
    """Get embedding for one text using Ollama."""
    r = requests.post(
        OLLAMA_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60
    )
    r.raise_for_status()
    emb = np.array(r.json()["embedding"], dtype="float32")
    if emb.shape[0] != EMBED_DIM:
        raise ValueError("Unexpected embedding size")
    return emb

# Embed texts in parallel with progress bar
def embed_batch_parallel(texts, max_workers=MAX_WORKERS):
    """Get embeddings for many texts at the same time."""
    embeddings_list = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(embed, t): i for i, t in enumerate(texts)}
        for f in tqdm(as_completed(futures), total=len(texts), desc="Embedding tickets", unit="ticket"):
            i = futures[f]
            embeddings_list[i] = f.result()
    return np.vstack(embeddings_list)

# Load Excel file
tqdm.write("Loading Excel")
df = pd.read_excel(DATA_PATH)

texts = []
metadata = []

for _, row in df.iterrows():
    text = f"""
    System: {row.get('systemName', '')}
    Complaint: {row.get('customerComplaint', '')}
    Fault: {row.get('faultText', '')}
    """.strip()
    texts.append(text)
    metadata.append(row.to_dict())

# Create embeddings
tqdm.write("Creating embeddings")
embeddings = embed_batch_parallel(texts)

# Normalize embeddings for cosine similarity
faiss.normalize_L2(embeddings)

# Build FAISS index
tqdm.write("Building FAISS index")
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

# Save index and metadata
faiss.write_index(index, str(INDEX_PATH))
pickle.dump(metadata, open(META_PATH, "wb"))

tqdm.write("Ingestion complete!")
