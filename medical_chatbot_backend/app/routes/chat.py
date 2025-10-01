from fastapi import APIRouter, HTTPException
from typing import List
from ..services.chat_service import ChatService
from ..models.schemas import ChatRequest, ChatResponse, SessionSummary

router = APIRouter()
chat_service = ChatService()

@router.get(
    "/chat/history",
    response_model=List[SessionSummary],
    summary="List chat sessions",
    description="Returns a list of chat sessions for the current in-memory store (demo).",
)
# PUBLIC_INTERFACE
def get_history():
    """List chat sessions with summary metadata."""
    sessions = chat_service.list_sessions()
    return [
        SessionSummary(
            id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at
        )
        for s in sessions
    ]

@router.get(
    "/chat/{session_id}",
    response_model=ChatResponse,
    summary="Get chat session",
    description="Returns messages and current recommendations for a particular session.",
)
# PUBLIC_INTERFACE
def get_session(session_id: str):
    """Fetch an existing chat session by ID, including recommendations."""
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    recs = chat_service.recommendations_for(session)
    return ChatResponse(id=session.id, messages=session.messages, recommendations=recs)

@router.get(
    "/chat/{session_id}/expert",
    response_model=List[str],
    summary="Expert recommendations (ClinicalAgent)",
    description=(
        "Return expert-style recommendations using the ClinicalAgent for the given session. "
        "Includes suggested tests/assessments, medicines/supportive care where appropriate, and a strong disclaimer."
    ),
)
# PUBLIC_INTERFACE
def get_session_expert_recommendations(session_id: str) -> List[str]:
    """
    Fetch expert recommendations for a chat session.

    Args:
        session_id: The chat session identifier.

    Returns:
        List[str]: Flattened list of expert suggestions derived from ClinicalAgent,
        including suggested tests, medicines/support, and a strong disclaimer.
    """
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_service.recommendations_expert_for(session)

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send message",
    description=(
        "Send a message to the assistant. "
        "If session_id is null or unknown, a new session will be created. "
        "Response includes messages and recommendations (with strong disclaimer)."
    ),
)
# PUBLIC_INTERFACE
def send_message(payload: ChatRequest):
    """
    Accepts user input, appends to session history, and returns updated conversation
    with recommendations from the MedicalAgent.
    """
    session = chat_service.handle_message(payload.session_id, payload.message)
    recs = chat_service.recommendations_for(session)
    return ChatResponse(id=session.id, messages=session.messages, recommendations=recs)
