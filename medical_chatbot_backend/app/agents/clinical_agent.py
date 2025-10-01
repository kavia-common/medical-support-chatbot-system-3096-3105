from typing import Dict, List, Tuple
from ..services.guidelines import load_vector_store
from ..models.schemas import DISLCAIMER_TEXT

class ClinicalAgent:
    """
    ClinicalAgent
    Purpose:
        Provide expert-style, actionable suggestions derived from a light RAG pass over the
        existing medical guidelines. It is distinct from PatientAgent (conversation triage) and
        MedicalAgent (general recommendations) by explicitly focusing on:
          - Suggested diagnostic tests or next steps
          - Suggested over-the-counter medicines or supportive care
        It always appends a strong medical disclaimer.

    Behavior:
        - Performs a top-k retrieval using the shared guideline vector store on the given query/context.
        - Heuristically extracts or proposes:
            * tests: e.g., ECG, troponin, chest X-ray if chest pain; temperature checks; etc.
            * medicines/support: generic, OTC guidance such as acetaminophen or ibuprofen if appropriate,
              hydration, honey/lozenges for cough (with safety caveats).
        - Output is structured as a dict with "tests", "medicines", and a "notes" list including the disclaimer.
          A flattened list can also be provided via recommend() for compatibility with the frontend.

    Usage:
        agent = ClinicalAgent()
        result = agent.suggest(user_query="I have chest pain with shortness of breath")
        # result = {"tests": [...], "medicines": [...], "notes": ["...disclaimer..."]}

        Or a simple flattened list:
        flat = agent.recommend("I have fever and cough")  # -> [ "...", "...", "Recommendations are not medical advice..." ]

    Inputs:
        user_query: str — Free text built from the conversation or the user's latest messages.
        k: int — Number of guideline snippets to retrieve.

    Outputs:
        suggest(): Dict[str, List[str]] with keys "tests", "medicines", "notes".
        recommend(): List[str] flattened list of all suggestions plus disclaimer.

    Disclaimer:
        All outputs include a strong medical disclaimer and must not be taken as medical advice.
    """

    def __init__(self):
        self.store = load_vector_store()

    def _extract_tests(self, user_query: str, retrieved_texts: List[str]) -> List[str]:
        """
        Heuristic extraction/creation of likely tests from the query and retrieved guideline texts.
        The logic is intentionally simple for demo purposes.
        """
        q = (user_query or "").lower()
        tests: List[str] = []

        # Chest pain patterns
        if "chest pain" in q or "chest tightness" in q:
            tests.extend([
                "Consider ECG (electrocardiogram) as an initial test.",
                "Consider troponin levels if clinically indicated.",
                "Chest X-ray may be considered where appropriate.",
                "If red flags (severe pain, dyspnea, syncope), seek urgent in-person evaluation."
            ])

        # Fever/cough patterns
        if "fever" in q or "cough" in q:
            tests.append("Check temperature and monitor duration/severity of fever.")
            # Encourage pulse oximetry when respiratory symptoms present
            if "cough" in q or "shortness of breath" in q:
                tests.append("If available, check oxygen saturation with a pulse oximeter; seek care if < 92% or worsening.")

        # Look for hints in retrieved texts (very basic keyword spotting)
        joined = " ".join(rt.lower() for rt in retrieved_texts)
        if "chest x-ray" in joined and "chest x-ray" not in [t.lower() for t in tests]:
            tests.append("Chest X-ray may aid evaluation based on symptoms and local practice.")
        if "ecg" in joined and not any("ecg" in t.lower() for t in tests):
            tests.append("ECG can be part of initial assessment for chest pain.")
        if "troponin" in joined and not any("troponin" in t.lower() for t in tests):
            tests.append("High-sensitivity troponin testing when indicated, per local protocols.")

        return tests

    def _extract_medicines(self, user_query: str, retrieved_texts: List[str]) -> List[str]:
        """
        Heuristic medicine/supportive care suggestions with safety caveats.
        """
        q = (user_query or "").lower()
        meds: List[str] = []

        if "fever" in q or "temperature" in q:
            meds.append("Over-the-counter antipyretic: acetaminophen (paracetamol), follow package dosing; never exceed max daily dose.")
            meds.append("Ibuprofen may be considered if appropriate; avoid with certain kidney, ulcer, or bleeding risks; take with food.")

        if "pain" in q or "headache" in q:
            meds.append("For mild to moderate pain/headache: acetaminophen as first-line; consider ibuprofen if appropriate.")

        if "cough" in q:
            meds.append("Hydration and throat lozenges may help cough. Consider simple cough suppressants per local guidance (short-term).")
            meds.append("Honey can help soothe cough (not for children under 1 year).")

        # Also scan retrieved for supportive care hints
        joined = " ".join(retrieved_texts).lower()
        if "hydration" in joined and not any("hydration" in m.lower() for m in meds):
            meds.append("Maintain adequate hydration and rest.")
        if "rest" in joined and not any("rest" in m.lower() for m in meds):
            meds.append("Ensure adequate rest while recovering.")

        return meds

    def _rag(self, user_query: str, k: int = 3) -> List[Tuple[str, str, float]]:
        """
        Internal helper to perform retrieval from the guideline store.
        Returns a list of (id, text, score).
        """
        return self.store.query(user_query or "general", k=k)

    def _dedupe(self, items: List[str]) -> List[str]:
        seen = set()
        out = []
        for i in items:
            key = (i or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(i)
        return out

    # PUBLIC_INTERFACE
    def suggest(self, user_query: str, k: int = 3) -> Dict[str, List[str]]:
        """
        Produce a structured clinical suggestion object using RAG on the shared guideline store.

        Args:
            user_query: Conversation/user text used to retrieve and tailor suggestions.
            k: Number of guideline snippets to retrieve.

        Returns:
            Dict with:
              - "tests": list of suggested tests/assessments
              - "medicines": list of suggested OTC medicines/support care items
              - "notes": list of general notes including the strong disclaimer
        """
        results = self._rag(user_query, k=k)
        retrieved_texts = [t for _, t, _ in results if "informational purposes only" not in t.lower()]

        tests = self._dedupe(self._extract_tests(user_query, retrieved_texts))
        meds = self._dedupe(self._extract_medicines(user_query, retrieved_texts))

        notes: List[str] = []
        # Include up to top 2 retrieved items as contextual notes (optional, trimmed)
        for text in retrieved_texts[:2]:
            notes.append(text)

        # Always include disclaimer at the end
        notes.append(DISLCAIMER_TEXT)
        notes = self._dedupe(notes)

        return {
            "tests": tests,
            "medicines": meds,
            "notes": notes,
        }

    # PUBLIC_INTERFACE
    def recommend(self, user_query: str, k: int = 3) -> List[str]:
        """
        Flattened list form of suggestions, convenient for existing frontend that expects a list of strings.

        Args:
            user_query: Conversation/user text used for retrieval.
            k: Number of guideline snippets to retrieve.

        Returns:
            List[str] of combined suggestions ending with a strong disclaimer.
        """
        bundle = self.suggest(user_query, k=k)
        flat: List[str] = []
        if bundle.get("tests"):
            flat.append("Suggested tests/assessments:")
            flat.extend(bundle["tests"])
        if bundle.get("medicines"):
            flat.append("Suggested medicines/support:")
            flat.extend(bundle["medicines"])
        if bundle.get("notes"):
            flat.extend(bundle["notes"])
        # Ensure disclaimer present even if notes empty
        if not any(DISLCAIMER_TEXT.lower() in s.lower() for s in flat):
            flat.append(DISLCAIMER_TEXT)
        return self._dedupe(flat) or [DISLCAIMER_TEXT]
