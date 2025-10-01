from typing import List
import hashlib
import math
import random

def _seeded_random_vector(text: str, dim: int) -> List[float]:
    """
    Generate a deterministic pseudo-random vector from text. For demo only.
    """
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    seed = int(h[:16], 16)
    rng = random.Random(seed)
    vec = [rng.uniform(-1, 1) for _ in range(dim)]
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

# PUBLIC_INTERFACE
def embed_text(text: str, dim: int = 384) -> List[float]:
    """Return a deterministic embedding vector for text (demo/mock)."""
    return _seeded_random_vector(text, dim)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)
