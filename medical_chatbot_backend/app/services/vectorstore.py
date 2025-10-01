from typing import List, Tuple
from .embeddings import embed_text, cosine_similarity
from ..config import settings

class VectorDoc:
    def __init__(self, id: str, text: str):
        self.id = id
        self.text = text
        self.vec = embed_text(text, dim=settings.VECTOR_DIM)

class SimpleVectorStore:
    """
    A minimal in-memory vector store for demo purposes.
    Supports naive KNN via linear scan.
    """
    def __init__(self):
        self.docs: List[VectorDoc] = []

    # PUBLIC_INTERFACE
    def add(self, id: str, text: str):
        """Add a document to the store keyed by id."""
        self.docs.append(VectorDoc(id=id, text=text))

    # PUBLIC_INTERFACE
    def query(self, query_text: str, k: int = 3) -> List[Tuple[str, str, float]]:
        """
        Search for top-k most similar documents.

        Returns:
            List of tuples (id, text, score)
        """
        if not self.docs:
            return []
        qvec = embed_text(query_text, dim=settings.VECTOR_DIM)
        scored = []
        for d in self.docs:
            score = cosine_similarity(qvec, d.vec)
            scored.append((d.id, d.text, score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:k]
