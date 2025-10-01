from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

DISLCAIMER_TEXT = "Recommendations are not medical advice. For informational purposes only."

class Message(BaseModel):
    role: str = Field(..., description="Role of the speaker: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(None, description="ISO timestamp for the message")

class ChatSession(BaseModel):
    id: str = Field(..., description="Unique session identifier")
    title: Optional[str] = Field(None, description="Optional title for the conversation")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    messages: List[Message] = Field(default_factory=list, description="Ordered list of messages")

class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Existing session ID to continue, or null to create new")
    message: str = Field(..., description="User's input message to send to the assistant")

class ChatResponse(BaseModel):
    id: str = Field(..., description="Session ID")
    messages: List[Message] = Field(..., description="Updated message list")
    recommendations: List[str] = Field(default_factory=list, description=f"Assistant recommendations. {DISLCAIMER_TEXT}")

class SessionSummary(BaseModel):
    id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(None, description="Readable title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")
