from typing import List
from ..services.guidelines import load_vector_store
from ..models.schemas import DISLCAIMER_TEXT

class MedicalAgent:
    """
    MedicalAgent uses simple RAG over a mock guidelines vector store to produce general recommendations.
    Adds light logic to include medicine suggestions for common cases (e.g., fever, pain),
    always with a strong disclaimer.
    """

    def __init__(self):
        self.store = load_vector_store()

    def _medicine_suggestions(self, user_query: str) -> List[str]:
        """
        Heuristic medicine suggestions with safety caveats.
        This is a demo; not medical advice.
        """
        q = (user_query or "").lower()
        meds: List[str] = []
        if "fever" in q or "temperature" in q:
            meds.append("Over-the-counter antipyretic: acetaminophen (paracetamol), follow package dosing; avoid exceeding daily limits.")
            meds.append("Alternative (if appropriate for you): ibuprofen with food; avoid if you have certain kidney, ulcer, or bleeding risks.")
        if "pain" in q or "headache" in q:
            meds.append("For mild to moderate pain or headache: acetaminophen as first-line; consider ibuprofen if appropriate for you.")
        if "cough" in q:
            meds.append("Hydration and throat lozenges may help. For bothersome cough, consider a simple cough suppressant as per local guidance.")
        # Keep medicines short and generic with safety warnings
        return meds

    # PUBLIC_INTERFACE
    def recommend(self, user_query: str, k: int = 3) -> List[str]:
        """
        Retrieve relevant guideline snippets and transform them into user-facing recommendations.
        Always includes a strong disclaimer. Adds brief medicine suggestions when appropriate.
        """
        results = self.store.query(user_query, k=k)
        recs: List[str] = []
        for _, text, score in results:
            # Filter out the disclaimer doc from ranking to avoid redundancy in content
            if "informational purposes only" in text.lower():
                continue
            recs.append(text)

        # Add minimal heuristic medicine suggestions if relevant to query
        med_suggestions = self._medicine_suggestions(user_query)
        if med_suggestions:
            recs.extend(med_suggestions)

        # Add explicit disclaimer as final entry
        recs.append(DISLCAIMER_TEXT)
        return recs or [DISLCAIMER_TEXT]
