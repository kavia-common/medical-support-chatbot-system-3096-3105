from app.services.chat_service import ChatService
from app.models.schemas import Message, ChatSession
from datetime import datetime

# PUBLIC_INTERFACE
def test_patient_agent_does_not_repeat_questions_and_marks_triage_complete():
    """Ensure PatientAgent tracks asked/answered and avoids repeating; triage_complete when base/conditional slots answered."""
    svc = ChatService()

    # Start a session and simulate conversation mentioning fever and pain (triggers conditional slots)
    s = svc.handle_message(None, "I have fever and pain since yesterday")
    sid = s.id

    # First assistant should ask base slots + temperature + pain location
    first_assistant = [m for m in s.messages if m.role == "assistant"][-1].content.lower()
    assert "how long have you had" in first_assistant
    assert "how severe" in first_assistant
    assert "any other associated" in first_assistant
    assert "measured your temperature" in first_assistant
    assert "where exactly is the pain" in first_assistant

    # Provide answers to all requested slots
    s = svc.handle_message(sid, "For 2 days, moderate, also cough.")
    s = svc.handle_message(sid, "Temperature was 38.2°C.")
    s = svc.handle_message(sid, "Pain is located on my right side.")

    # Next assistant response should not repeat slot questions; should move to summary guidance
    last_assistant = [m for m in s.messages if m.role == "assistant"][-1].content.lower()
    assert "thanks for the details" not in last_assistant  # no more prompt bundle
    assert "summarize and provide general guidance" in last_assistant

    # triage_complete should be True so medicines can be suggested
    recs = svc.recommendations_for(s)
    meds_present = any("acetaminophen" in r.lower() or "ibuprofen" in r.lower() for r in recs)
    assert meds_present, "Medicine suggestions should appear after triage is complete"

# PUBLIC_INTERFACE
def test_medical_agent_meds_gated_until_triage_complete():
    """Medicine suggestions should be withheld until triage is marked complete."""
    svc = ChatService()

    # Start a session with fever mention
    s = svc.handle_message(None, "I have a mild fever and cough.")
    # Immediately request recommendations (triage not complete yet)
    recs = svc.recommendations_for(s)
    meds_present = any("acetaminophen" in r.lower() or "ibuprofen" in r.lower() for r in recs)
    assert not meds_present, "Medicine suggestions should not appear before triage completion"

    # Answer base questions and temperature
    sid = s.id
    s = svc.handle_message(sid, "For 3 days, mild, also sore throat.")
    s = svc.handle_message(sid, "My temperature was 38C.")
    # No pain location needed if no pain mentioned, so triage should now be complete
    recs2 = svc.recommendations_for(s)
    meds_present2 = any("acetaminophen" in r.lower() or "ibuprofen" in r.lower() for r in recs2)
    assert meds_present2, "Medicine suggestions should appear after triage completion"
