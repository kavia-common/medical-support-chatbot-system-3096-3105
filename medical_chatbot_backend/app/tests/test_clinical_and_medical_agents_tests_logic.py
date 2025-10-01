from app.agents.clinical_agent import ClinicalAgent
from app.agents.medical_agent import MedicalAgent

# PUBLIC_INTERFACE
def test_clinical_agent_chest_pain_emits_chest_tests_only_with_context():
    """Chest pain context should produce ECG/troponin/CXR suggestions (linked to guidelines)."""
    agent = ClinicalAgent()
    q = "I have chest pain and shortness of breath for 2 hours."
    flat = agent.recommend(q)
    joined = " ".join(s.lower() for s in flat)
    assert "ecg" in joined, "ECG should be suggested for chest pain context"
    assert "troponin" in joined, "Troponin should be suggested for chest pain context"
    assert "x-ray" in joined, "Chest X-ray should be suggested for chest pain context"

# PUBLIC_INTERFACE
def test_clinical_agent_cough_without_chest_pain_does_not_emit_chest_tests():
    """Cough alone should not trigger chest-pain specific tests; should allow SpO2 check at most."""
    agent = ClinicalAgent()
    q = "I have a mild cough for 3 days, no chest pain."
    flat = agent.recommend(q)
    lower = [s.lower() for s in flat]
    # Should not include chest-pain specific tests
    assert not any("ecg" in s or "troponin" in s for s in lower), "ECG/Troponin should not be suggested for isolated cough"
    # May include pulse oximetry check due to respiratory context
    assert any("oximetry" in s or "spo2" in s for s in lower), "SpO2 check should be allowed for respiratory symptoms"

# PUBLIC_INTERFACE
def test_medical_agent_meds_are_symptom_linked():
    """MedicalAgent medicine suggestions should only appear if corresponding symptoms are present in the query."""
    agent = MedicalAgent()
    # No relevant symptom: expect no meds, only disclaimer/context
    none_q = "I would like general wellness info."
    flat_none = agent.recommend(none_q, allow_meds=True)
    assert not any("acetaminophen" in s.lower() or "ibuprofen" in s.lower() or "cough" in s.lower() for s in flat_none), \
        "No meds should appear without symptom triggers"

    # Fever symptom present: expect antipyretics
    fever_q = "Fever of 38C for two days."
    flat_fever = agent.recommend(fever_q, allow_meds=True)
    assert any("acetaminophen" in s.lower() for s in flat_fever), "Antipyretic should appear when fever present"

    # Cough symptom present: expect cough supportive suggestion
    cough_q = "Persistent cough at night."
    flat_cough = agent.recommend(cough_q, allow_meds=True)
    assert any("cough suppressant" in s.lower() or "throat lozenges" in s.lower() for s in flat_cough), \
        "Cough supportive care should appear when cough present"
