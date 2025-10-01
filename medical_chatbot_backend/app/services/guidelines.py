from typing import List, Dict
from .vectorstore import SimpleVectorStore

GUIDELINES: List[Dict[str, str]] = [
    {
        "id": "cough_fever_general",
        "text": (
            "For patients with cough and fever of 3+ days, consider viral etiologies. "
            "Assess for red flags: shortness of breath at rest, chest pain, confusion, cyanosis, "
            "oxygen saturation < 92%. Recommend hydration, rest, and antipyretics like acetaminophen "
            "as appropriate. If symptoms persist or worsen, seek medical care."
        ),
    },
    {
        "id": "cough_medicine_support",
        "text": (
            "Cough supportive care: hydration, honey (not for children under 1), and throat lozenges. "
            "Consider simple cough suppressants per local guidelines for short-term relief."
        ),
    },
    {
        "id": "fever_antipyretics",
        "text": (
            "Fever management: consider acetaminophen (paracetamol) as first-line antipyretic, "
            "following package dosing and never exceeding maximum daily dose. "
            "Ibuprofen can be considered if appropriate for the individual (avoid in certain kidney, ulcer, or bleeding risks)."
        ),
    },
    {
        "id": "chest_pain_tests",
        "text": (
            "Chest pain evaluation: assess onset, character, radiation, associated symptoms. "
            "Initial tests may include ECG, troponin, chest X-ray. Red flags necessitate urgent evaluation."
        ),
    },
    {
        "id": "headache_nausea",
        "text": (
            "Post-prandial headache and nausea may indicate migraine or reflux among other causes. "
            "Consider dietary triggers, hydration, sleep hygiene. If severe or frequent, consult a clinician."
        ),
    },
    {
        "id": "pain_general_analgesia",
        "text": (
            "For mild to moderate pain or headache, consider acetaminophen first-line. "
            "Ibuprofen may help if appropriate; take with food. Review contraindications and always follow label instructions."
        ),
    },
    {
        "id": "disclaimer",
        "text": (
            "Recommendations are not medical advice. For informational purposes only. "
            "Always consult a qualified healthcare professional."
        ),
    },
]

# PUBLIC_INTERFACE
def load_vector_store() -> SimpleVectorStore:
    """Load guidelines into a simple in-memory vector store (demo)."""
    store = SimpleVectorStore()
    for g in GUIDELINES:
        store.add(g["id"], g["text"])
    return store
