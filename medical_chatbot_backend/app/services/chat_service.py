import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Any

from ..models.schemas import ChatSession, Message
from ..agents.patient_agent import PatientAgent
from ..agents.medical_agent import MedicalAgent
from ..agents.clinical_agent import ClinicalAgent

def _strip_slot_markers(text: str) -> str:
    """
    Remove any [slot:...] markers from assistant text before exposing/storing for RAG relevance.
    """
    if not text:
        return text
    parts = []
    for token in text.split():
        if token.startswith("[slot:"):
            continue
        parts.append(token)
    return " ".join(parts)

class ChatService:
    """
    In-memory chat session manager. For demo purposes.
    Also keeps per-session memory for asked/answered slots and triage completion
    to avoid repeating questions and to gate medicine suggestions until triage is complete.
    """

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.patient_agent = PatientAgent()
        self.medical_agent = MedicalAgent()
        self.clinical_agent = ClinicalAgent()
        # Session memory keyed by session id
        self.session_state: Dict[str, Dict[str, Any]] = {}

    def _ensure_state(self, sid: str) -> Dict[str, Any]:
        state = self.session_state.get(sid)
        if not state:
            state = {
                "asked_slots": set(),       # type: Set[str]
                "answered_slots": set(),    # type: Set[str]
                "triage_complete": False,   # type: bool
            }
            self.session_state[sid] = state
        return state

    # PUBLIC_INTERFACE
    def list_sessions(self) -> List[ChatSession]:
        """Return all chat sessions sorted by updated time desc."""
        return sorted(self.sessions.values(), key=lambda s: s.updated_at, reverse=True)

    # PUBLIC_INTERFACE
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by id."""
        return self.sessions.get(session_id)

    # PUBLIC_INTERFACE
    def handle_message(self, session_id: Optional[str], user_text: str) -> ChatSession:
        """
        Process a user message. Create a session if needed, append user message,
        and have PatientAgent respond.
        Session-level memory is passed to PatientAgent to prevent repeated questions.
        """
        now = datetime.utcnow()
        if not session_id or session_id not in self.sessions:
            sid = str(uuid.uuid4())
            self.sessions[sid] = ChatSession(
                id=sid,
                title=(user_text[:48] + "…") if len(user_text) > 48 else user_text,
                created_at=now,
                updated_at=now,
                messages=[],
            )
            session = self.sessions[sid]
        else:
            session = self.sessions[session_id]
            session.updated_at = now

        # Ensure state exists
        state = self._ensure_state(session.id)

        # Add user message
        session.messages.append(
            Message(role="user", content=user_text, timestamp=now)
        )

        # PatientAgent response with stateful slot tracking
        reply_text, updated_state = self.patient_agent.respond(
            session.messages, user_text, asked_slots=set(state["asked_slots"]), answered_slots=set(state["answered_slots"])
        )
        # Update state from patient agent (asked/answered/triage_complete)
        state["asked_slots"] = set(updated_state.get("asked_slots", set()))
        state["answered_slots"] = set(updated_state.get("answered_slots", set()))
        state["triage_complete"] = bool(updated_state.get("triage_complete", False))

        # Store assistant message but strip markers for user-facing display
        clean_reply = _strip_slot_markers(reply_text)
        session.messages.append(
            Message(role="assistant", content=clean_reply, timestamp=datetime.utcnow())
        )

        # Update title if not set
        if not session.title:
            session.title = user_text[:50]

        return session

    # PUBLIC_INTERFACE
    def recommendations_for(self, session: ChatSession) -> List[str]:
        """
        Generate recommendations for the latest context by combining the last few user queries.
        Medicine suggestions are only provided if triage is marked complete for this session.
        """
        state = self.session_state.get(session.id, {})
        triage_complete = bool(state.get("triage_complete", False))

        # Combine last N user utterances (e.g., 3) for a richer query
        last_user_texts = [m.content for m in session.messages if m.role == "user"][-3:]
        if not last_user_texts:
            # Fallback to last assistant/user if user is missing
            last_user = next((m for m in reversed(session.messages) if m.role == "user"), None)
            query = last_user.content if last_user else (session.messages[-1].content if session.messages else "")
        else:
            query = " ".join(last_user_texts)

        return self.medical_agent.recommend(query or "general", allow_meds=triage_complete)

    # PUBLIC_INTERFACE
    def recommendations_expert_for(self, session: ChatSession) -> List[str]:
        """
        Generate expert-style recommendations using the ClinicalAgent.

        Notes:
            - This call ignores the triage gate for medicines because ClinicalAgent is designed
              to produce an expert bundle; however, you may choose to respect triage by modifying
              this method if desired.
            - Returns a flattened list of suggestions suitable for the existing frontend's
              recommendations panel.
        """
        # Use the same query construction as recommendations_for
        last_user_texts = [m.content for m in session.messages if m.role == "user"][-3:]
        if not last_user_texts:
            last_user = next((m for m in reversed(session.messages) if m.role == "user"), None)
            query = last_user.content if last_user else (session.messages[-1].content if session.messages else "")
        else:
            query = " ".join(last_user_texts)
        return self.clinical_agent.recommend(query or "general")
