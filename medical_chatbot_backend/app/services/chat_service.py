import uuid
from datetime import datetime
from typing import Dict, List, Optional

from ..models.schemas import ChatSession, Message
from ..agents.patient_agent import PatientAgent
from ..agents.medical_agent import MedicalAgent

class ChatService:
    """
    In-memory chat session manager. For demo purposes.
    """

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.patient_agent = PatientAgent()
        self.medical_agent = MedicalAgent()

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
        have PatientAgent respond, and fetch MedicalAgent recommendations.
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

        # Add user message
        session.messages.append(
            Message(role="user", content=user_text, timestamp=now)
        )

        # PatientAgent response
        reply_text = self.patient_agent.respond(session.messages, user_text)
        session.messages.append(
            Message(role="assistant", content=reply_text, timestamp=datetime.utcnow())
        )

        # Update title if not set
        if not session.title:
            session.title = user_text[:50]

        # Recommendations via MedicalAgent
        return session

    # PUBLIC_INTERFACE
    def recommendations_for(self, session: ChatSession) -> List[str]:
        """Generate recommendations for the latest user query using MedicalAgent."""
        last_user = next((m for m in reversed(session.messages) if m.role == "user"), None)
        query = last_user.content if last_user else (session.messages[-1].content if session.messages else "")
        return self.medical_agent.recommend(query or "general")
