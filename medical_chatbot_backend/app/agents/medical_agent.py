from typing import List
from ..services.guidelines import load_vector_store
from ..models.schemas import DISLCAIMER_TEXT

class MedicalAgent:
    """
    MedicalAgent uses simple RAG over a mock guidelines vector store to produce general recommendations.
    """

    def __init__(self):
        self.store = load_vector_store()

    # PUBLIC_INTERFACE
    def recommend(self, user_query: str, k: int = 3) -> List[str]:
        """
        Retrieve relevant guideline snippets and transform them into user-facing recommendations.
        Always includes a strong disclaimer.
        """
        results = self.store.query(user_query, k=k)
        recs: List[str] = []
        for _, text, score in results:
            # Filter out the disclaimer doc from ranking to avoid redundancy in content
            if "informational purposes only" in text.lower():
                continue
            recs.append(text)
        # Add explicit disclaimer as final entry
        recs.append(DISLCAIMER_TEXT)
        return recs or [DISLCAIMER_TEXT]
