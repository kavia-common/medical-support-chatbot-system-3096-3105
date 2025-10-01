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

    RAG linkage:
    - Builds a symptom-rich query from conversation and slot state to ensure that both
      MedicalAgent and ClinicalAgent retrieval is explicitly tied to the user's relevant symptoms.
    """

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.patient_agent = PatientAgent()
        self.medical_agent = MedicalAgent()
        self.clinical_agent = ClinicalAgent()
        # Session memory keyed by session id
        # Use only JSON-serializable primitives for potential future persistence
        self.session_state: Dict[str, Dict[str, Any]] = {}

    def _ensure_state(self, sid: str) -> Dict[str, Any]:
        state = self.session_state.get(sid)
        if not state:
            state = {
                "asked_slots": [],        # List[str]
                "answered_slots": [],     # List[str]
                "triage_complete": False, # bool
            }
            self.session_state[sid] = state
        else:
            # Defensive normalization
            state["asked_slots"] = list(state.get("asked_slots") or [])
            state["answered_slots"] = list(state.get("answered_slots") or [])
            state["triage_complete"] = bool(state.get("triage_complete", False))
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

        # Prepare sets from serialized lists
        asked_set = set(state["asked_slots"])
        answered_set = set(state["answered_slots"])

        # PatientAgent response with stateful slot tracking
        reply_text, updated_state = self.patient_agent.respond(
            session.messages, user_text, asked_slots=asked_set, answered_slots=answered_set
        )

        # Update state from patient agent (asked/answered/triage_complete) and store back as lists
        state["asked_slots"] = sorted(list(set(updated_state.get("asked_slots", set()))))
        state["answered_slots"] = sorted(list(set(updated_state.get("answered_slots", set()))))
        state["triage_complete"] = bool(updated_state.get("triage_complete", False))

        # Store assistant message but strip markers for user-facing display
        clean_reply = _strip_slot_markers(reply_text)
        session.messages.append(
            Message(role="assistant", content=clean_reply, timestamp=datetime.utcnow())
        )

        # Update title if not set or too generic
        if not session.title:
            session.title = user_text[:50]

        return session

    def _build_rag_context(self, session: ChatSession) -> str:
        """
        Build a symptom-rich RAG query using:
        - Recent user utterances
        - Detected slot state (asked/answered) to bias context (e.g., fever -> include temperature)
        - Simple symptom keyphrase detection from full history
        This ensures guideline retrieval is tightly linked to the user's relevant symptoms.
        """
        # Recent user messages
        last_users = [m.content for m in session.messages if m.role == "user"][-5:]
        recent = " ".join(last_users)

        # Full-text user history for additional hints
        user_hist = " ".join([m.content for m in session.messages if m.role == "user"]).lower()

        # Pull current session slot state if any
        st = self.session_state.get(session.id, {})
        answered = set(st.get("answered_slots") or [])
        asked = set(st.get("asked_slots") or [])

        # Heuristic symptom flags from history (kept minimal, deterministic)
        flags = []
        if any(k in user_hist for k in ["fever", "temperature", "temp"]):
            flags.append("symptom:fever")
            if "temperature" in answered:
                flags.append("answered:temperature")
        if any(k in user_hist for k in ["cough"]):
            flags.append("symptom:cough")
        if any(k in user_hist for k in ["chest pain", "chest tightness"]):
            flags.append("symptom:chest_pain")
            if "pain_location" in answered or "pain_location" in asked:
                flags.append("context:pain_location_known_or_asked")
        if any(k in user_hist for k in ["headache"]):
            flags.append("symptom:headache")
        if any(k in user_hist for k in ["nausea"]):
            flags.append("symptom:nausea")
        if any(k in user_hist for k in ["shortness of breath", "dyspnea"]):
            flags.append("symptom:shortness_of_breath")

        # Include core triage slots to bias retrieval if present
        if "duration" in answered:
            flags.append("answered:duration")
        if "severity" in answered:
            flags.append("answered:severity")
        if "associated" in answered:
            flags.append("answered:associated")

        # Create a compact, explicit query – recent context + normalized flags
        normalized_flags = " ".join(sorted(set(flags)))
        query = f"{recent} || {normalized_flags}".strip()
        return query or user_hist or "general"

    # PUBLIC_INTERFACE
    def recommendations_for(self, session: ChatSession) -> List[str]:
        """
        Generate recommendations for the latest context using a symptom-rich query.
        Medicine suggestions are only provided if triage is marked complete for this session.
        """
        state = self.session_state.get(session.id, {})
        triage_complete = bool(state.get("triage_complete", False))

        # Build explicit symptom-aware query for RAG
        query = self._build_rag_context(session)

        return self.medical_agent.recommend(query or "general", allow_meds=triage_complete)

    def recommendations_expert_for(self, session: ChatSession) -> List[str]:
        """
        Generate expert-style recommendations using the ClinicalAgent with the same
        symptom-rich context to tightly couple tests/medicines to user symptoms and
        retrieved guidelines.
        """
        query = self._build_rag_context(session)
        return self.clinical_agent.recommend(query or "general")
