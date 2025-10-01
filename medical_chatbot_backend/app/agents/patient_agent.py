from typing import Dict, List
from datetime import datetime
from ..models.schemas import Message

class PatientAgent:
    """
    PatientAgent handles conversational structure, gathers symptoms interactively,
    and produces succinct structured notes.
    """

    def __init__(self):
        pass

    # PUBLIC_INTERFACE
    def respond(self, history: List[Message], user_text: str) -> str:
        """
        Generate a conversational response to collect details.
        Uses simple heuristics to ask about duration, severity, and associated symptoms.
        """
        lower = user_text.lower()
        prompts: List[str] = []

        if not any(k in lower for k in ["day", "week", "month", "year", "hours", "hour"]):
            prompts.append("How long have you had these symptoms?")
        if not any(k in lower for k in ["mild", "moderate", "severe", "scale", "out of 10"]):
            prompts.append("How severe are they (mild/moderate/severe or 1-10)?")
        if not any(k in lower for k in ["associated", "with", "along with", "also"]):
            prompts.append("Any other associated symptoms?")
        if "fever" in lower and "temperature" not in lower:
            prompts.append("Have you measured your temperature? What was it?")
        if "pain" in lower and "location" not in lower:
            prompts.append("Where exactly is the pain located?")

        if prompts:
            return "Thanks for the details. " + " ".join(prompts)

        return (
            "Thank you. I will summarize and provide general guidance. "
            "Please remember: this is not medical advice."
        )

    # PUBLIC_INTERFACE
    def structure_notes(self, history: List[Message]) -> Dict[str, str]:
        """
        Create simple structured notes based on the conversation.
        Returns a dictionary with sections for demo purposes.
        """
        user_inputs = [m.content for m in history if m.role == "user"]
        assistant_inputs = [m.content for m in history if m.role == "assistant"]
        summary = " ".join(user_inputs[-3:]).strip() or "No summary available."
        questions = " ".join(assistant_inputs[-2:]).strip() or "No specific questions asked."
        return {
            "chief_complaint": user_inputs[0] if user_inputs else "N/A",
            "history_of_present_illness": summary,
            "key_questions": questions,
            "timestamp": datetime.utcnow().isoformat(),
        }
