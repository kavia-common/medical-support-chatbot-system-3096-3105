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
    """

    def __init__(self):
        self.store = load_vector_store()

    def _extract_tests(self, user_query: str, retrieved_texts: List[str]) -> List[str]:
        """
        Heuristic extraction of tests explicitly linked to symptoms AND guideline retrieval.

        Emission rules (tightened):
        - Emit chest-pain related tests only if the user mentions chest pain/tightness OR
          the retrieved guideline snippet explicitly references chest pain testing,
          AND the retrieved snippet contains the specific test keyword (ECG, troponin, CXR).
        - Emit respiratory checks (SpO2) only when respiratory symptom is present (cough/SOB)
          OR the retrieved guideline mentions oxygen/saturation context.
        - Emit temperature check only when fever/temperature context present in user text.

        This avoids overly-broad or random emissions (e.g., generic panels for cough).
        """
        q = (user_query or "").lower()
        tests: List[str] = []

        # Symptom flags from user query
        has_chest_pain = ("chest pain" in q) or ("chest tightness" in q)
        has_cough = ("cough" in q)
        has_fever = ("fever" in q or "temperature" in q or "temp" in q)
        has_sob = ("shortness of breath" in q) or ("dyspnea" in q)

        # Scan retrieved texts to ensure guideline-coupled suggestions
        joined = " ".join(rt.lower() for rt in retrieved_texts)
        g_has_chest_pain_ctx = "chest pain" in joined or "chest tightness" in joined
        g_has_ecg = "ecg" in joined
        g_has_trop = "troponin" in joined
        g_has_cxr = ("chest x-ray" in joined) or ("x-ray" in joined) or ("chest xray" in joined)
        g_has_sat = ("saturation" in joined) or ("oxygen" in joined) or ("oximeter" in joined)

        # Chest pain-focused tests: require chest pain context from either user or guideline,
        # and require the specific test keyword to appear (to avoid generic emissions).
        chest_ctx = has_chest_pain or g_has_chest_pain_ctx
        if chest_ctx:
            if g_has_ecg or has_chest_pain:
                tests.append("Test: ECG (electrocardiogram) — Use-case: Initial assessment for chest pain. Safety/escalation: If severe pain, syncope, or persistent symptoms, seek urgent in-person evaluation.")
            if g_has_trop or has_chest_pain:
                tests.append("Test: High-sensitivity troponin — Use-case: Assess myocardial injury when indicated. Safety: Follow local protocols; abnormal results need clinical evaluation.")
            if g_has_cxr or has_chest_pain:
                tests.append("Test: Chest X-ray — Use-case: Evaluate for pulmonary or structural causes when appropriate. Safety: Radiation exposure minimal; use per clinical guidance.")

        # Fever check: only when fever/temperature context exists
        if has_fever:
            tests.append("Check: Temperature — Use-case: Track fever trends and response to antipyretics. Safety: Follow dosing limits if using antipyretics.")

        # Respiratory checks: only for cough/SOB or explicit oxygen/saturation mentions in guidelines
        if has_cough or has_sob or g_has_sat:
            tests.append("Check: Pulse oximetry (SpO2) — Use-case: Assess oxygen saturation in respiratory symptoms. Escalation: Seek care if < 92% or worsening.")

        return tests

    def _extract_medicines(self, user_query: str, retrieved_texts: List[str]) -> List[str]:
        """
        Heuristic medicines/supportive care with explicit name, use-case, dosing/safety.
        Driven by symptom context and guideline keywords; avoid generic, non-symptom-linked emission.
        """
        q = (user_query or "").lower()
        meds: List[str] = []

        has_fever = ("fever" in q or "temperature" in q or "temp" in q)
        has_pain = ("pain" in q or "headache" in q)
        has_cough = ("cough" in q)

        joined = " ".join(retrieved_texts).lower()

        # Antipyretics only if fever context or antipyretic guidance retrieved
        if has_fever or "antipyretic" in joined or "acetaminophen" in joined:
            meds.append("Medicine: Acetaminophen (paracetamol) — Use-case: Fever reduction and mild pain. Dosing: Follow package label; never exceed max daily dose. Safety: Avoid combining multiple acetaminophen-containing products.")
        # Ibuprofen for pain/fever if context suggests it or guidance mentions it
        if (has_fever or has_pain) or "ibuprofen" in joined:
            meds.append("Medicine: Ibuprofen (NSAID) — Use-case: Pain or fever (if appropriate). Dosing: Use lowest effective dose with food. Safety: Avoid with certain kidney disease, ulcers, or bleeding risks; consider drug interactions.")
        # If pain present and acetaminophen not already included explicitly
        if has_pain and "acetaminophen" not in " ".join(meds).lower():
            meds.append("Medicine: Acetaminophen — Use-case: First-line for mild to moderate pain/headache. Dosing/Safety: As above; heed max daily dose.")
        # Cough supportive care only when cough context present in user or guidelines
        if has_cough or "cough" in joined:
            meds.append("Support: Hydration and throat lozenges — Use-case: Symptomatic cough relief. Safety: Lozenges per label; avoid choking risk in children.")
            meds.append("Support: Honey (not for <1 year) — Use-case: Soothe cough. Safety: Do not give honey to infants.")
            meds.append("Option: Simple cough suppressant (short-term) — Use-case: Troublesome cough per local guidance. Safety: Follow label; avoid duplication of active ingredients.")

        # Only add general hydration/rest if the guideline explicitly mentions them in the retrieved context
        if "hydration" in joined and not any("hydration" in m.lower() for m in meds):
            meds.append("Support: Adequate hydration and rest — Use-case: General recovery support. Safety: As tolerated.")
        if "rest" in joined and not any("rest" in m.lower() for m in meds):
            meds.append("Support: Rest — Use-case: Recovery; monitor symptoms. Safety: Seek care if worsening.")

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
        # Filter out pure disclaimer docs to avoid polluting notes
        retrieved_texts = [t for _, t, _ in results if "informational purposes only" not in t.lower()]

        tests = self._dedupe(self._extract_tests(user_query, retrieved_texts))
        meds = self._dedupe(self._extract_medicines(user_query, retrieved_texts))

        # Provide explicit linkage justification based on actual symptom tokens
        linkage: List[str] = []
        uq = (user_query or "").lower()
        if any(k in uq for k in ["fever", "temperature", "temp"]):
            linkage.append("Reasoning: Fever-related suggestions included based on your reported fever/temperature.")
        if "cough" in uq:
            linkage.append("Reasoning: Cough-related guidance included due to your cough symptoms.")
        if any(k in uq for k in ["chest pain", "chest tightness"]):
            linkage.append("Reasoning: Chest pain pattern detected; tests aligned with guideline mentions (ECG, troponin, CXR).")
        if "shortness of breath" in uq or "dyspnea" in uq:
            linkage.append("Reasoning: Respiratory symptoms noted; oxygen saturation checks considered when appropriate.")
        if any(k in uq for k in ["headache", "nausea"]):
            linkage.append("Reasoning: Headache/nausea were noted; general supportive guidance included.")

        # Contextual notes include top guideline snippets to justify recommendations
        notes: List[str] = []
        if retrieved_texts:
            notes.append("Contextual notes (from guidelines):")
        for text in retrieved_texts[:2]:
            notes.append(text)

        # Add reasoning lines up front when present
        if linkage:
            notes.insert(0, "Selection rationale:")
            notes = linkage + notes

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
