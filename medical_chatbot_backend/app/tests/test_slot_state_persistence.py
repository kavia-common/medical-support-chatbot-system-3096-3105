# PUBLIC_INTERFACE
def test_slot_state_persists_and_no_repetition():
    """Ensure asked/answered slot state persists across multiple turns and prevents repeated questions."""
    from app.services.chat_service import ChatService

    svc = ChatService()
    s = svc.handle_message(None, "I have fever and chest pain since last night.")
    sid = s.id

    # Assistant should ask base + temp + pain_location on first turn
    first_reply = [m for m in s.messages if m.role == "assistant"][-1].content.lower()
    assert "how long have you had" in first_reply
    assert "how severe" in first_reply
    assert "any other associated" in first_reply
    assert "measured your temperature" in first_reply
    assert "where exactly is the pain" in first_reply

    # Provide partial answers across multiple turns
    s = svc.handle_message(sid, "For 1 day, mild.")
    s = svc.handle_message(sid, "Also shortness of breath.")
    # Provide temperature later
    s = svc.handle_message(sid, "Temperature was 38.1C.")
    # Provide pain location later
    s = svc.handle_message(sid, "Pain is located in the center of my chest.")

    # Now assistant should not ask any more slot questions and should proceed
    last_reply = [m for m in s.messages if m.role == "assistant"][-1].content.lower()
    assert "how long have you had" not in last_reply
    assert "how severe" not in last_reply
    assert "any other associated" not in last_reply
    assert "measured your temperature" not in last_reply
    assert "where exactly is the pain" not in last_reply
    assert "summarize and provide general guidance" in last_reply
