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

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        seen = set()
        out = []
        for it in items:
            key = (it or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    # PUBLIC_INTERFACE
    def recommend(self, user_query: str, k: int = 3, allow_meds: bool = True) -> List[str]:
        """
        Retrieve relevant guideline snippets and transform them into user-facing recommendations.
        Always includes a strong disclaimer. Adds brief medicine suggestions when appropriate.

        Args:
            user_query: Combined user utterances used to search and tailor suggestions.
            k: Number of guideline snippets to retrieve.
            allow_meds: If False, medicine suggestions are withheld until triage completion.
        """
        # Deterministic retrieval for given query using mock embeddings; filter disclaimer doc
        results = self.store.query(user_query or "general", k=max(1, k))
        core: List[str] = []
        for _, text, _ in results:
            if "informational purposes only" in text.lower():
                continue
            core.append(text)

        recs: List[str] = []
        if core:
            recs.append("Contextual guidance (linked to your symptoms):")
            recs.extend(core[:3])

        # Add minimal heuristic medicine suggestions if relevant to query AND allowed
        if allow_meds:
            med_suggestions = self._medicine_suggestions(user_query)
            if med_suggestions:
                recs.append("Possible OTC/support (symptom-linked, if appropriate):")
                recs.extend(med_suggestions[:3])

        # Remove duplicates while preserving ordering and trim to a reasonable size
        recs = self._dedupe_preserve_order(recs)[: 6]

        # Add explicit disclaimer as final entry (ensure single instance)
        if not any(DISLCAIMER_TEXT.lower() in (r or "").lower() for r in recs):
            recs.append(DISLCAIMER_TEXT)
        return recs or [DISLCAIMER_TEXT]
