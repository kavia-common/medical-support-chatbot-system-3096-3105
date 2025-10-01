from typing import Dict, List, Set
from datetime import datetime
from ..models.schemas import Message

class PatientAgent:
    """
    PatientAgent handles conversational structure, gathers symptoms interactively,
    and produces succinct structured notes.

    Strategy to avoid repetition:
    - Infer which slots were ALREADY ASKED from prior assistant messages by scanning for markers.
    - Infer which slots are ALREADY ANSWERED from user messages by scanning for keywords.
    - Only ask about slots that are neither asked nor answered.
    Slots: duration, severity, associated symptoms, temperature (if fever mentioned), pain location (if pain mentioned).
    """

    def __init__(self):
        # Slot marker tokens we will embed when asking questions to help future turns avoid repeats
        self.SLOT_MARKERS = {
            "duration": "[slot:duration]",
            "severity": "[slot:severity]",
            "associated": "[slot:associated]",
            "temperature": "[slot:temperature]",
            "pain_location": "[slot:pain_location]",
        }

    def _asked_slots(self, history: List[Message]) -> Set[str]:
        asked: Set[str] = set()
        for m in history:
            if m.role != "assistant":
                continue
            text = (m.content or "").lower()
            for slot, token in self.SLOT_MARKERS.items():
                if token in text:
                    asked.add(slot)
        return asked

    def _answered_slots(self, history: List[Message]) -> Set[str]:
        answered: Set[str] = set()
        # Examine last few user messages to infer responses
        user_msgs = [m.content.lower() for m in history if m.role == "user"][-5:]
        text = " ".join(user_msgs)

        # Heuristics for slot completion
        if any(k in text for k in ["day", "days", "week", "weeks", "month", "months", "year", "years", "hour", "hours"]):
            answered.add("duration")
        if any(k in text for k in ["mild", "moderate", "severe"]) or any(k in text for k in ["1/10", "2/10","3/10","4/10","5/10","6/10","7/10","8/10","9/10","10/10"]) or "out of 10" in text:
            answered.add("severity")
        if any(k in text for k in ["associated", "along with", "also", "in addition", "other symptoms"]):
            answered.add("associated")
        if "temperature" in text or any(k in text for k in ["°c", "°f", "fever of", "temp"]):
            answered.add("temperature")
        if any(k in text for k in ["pain in", "hurts in", "located", "location", "at my", "on my"]):
            answered.add("pain_location")

        # Conditional slots inferred by trigger mentions
        # If fever is not mentioned anywhere in recent user text, we don't need to consider temperature slot.
        # If pain is not mentioned, skip pain_location slot.
        return answered

    def _needs_temperature(self, history: List[Message], current_user_text: str) -> bool:
        text = (current_user_text or "").lower() + " " + " ".join(
            [m.content.lower() for m in history if m.role == "user"][-4:]
        )
        return ("fever" in text)

    def _needs_pain_location(self, history: List[Message], current_user_text: str) -> bool:
        text = (current_user_text or "").lower() + " " + " ".join(
            [m.content.lower() for m in history if m.role == "user"][-4:]
        )
        return ("pain" in text)

    # PUBLIC_INTERFACE
    def respond(self, history: List[Message], user_text: str) -> str:
        """
        Generate a conversational response to collect details.
        Avoids repeating prior questions by tracking slot markers in assistant messages and
        inferring answered slots from recent user messages.
        """
        lower = user_text.lower()
        prompts: List[str] = []

        asked = self._asked_slots(history)
        answered = self._answered_slots(history)

        # Base slots: duration, severity, associated
        if "duration" not in asked and "duration" not in answered:
            prompts.append(f"{self.SLOT_MARKERS['duration']} How long have you had these symptoms?")
        if "severity" not in asked and "severity" not in answered:
            prompts.append(f"{self.SLOT_MARKERS['severity']} How severe are they (mild/moderate/severe or 1-10)?")
        if "associated" not in asked and "associated" not in answered:
            prompts.append(f"{self.SLOT_MARKERS['associated']} Any other associated symptoms?")

        # Conditional slots
        if self._needs_temperature(history, user_text) and "temperature" not in asked and "temperature" not in answered and "temperature" not in lower:
            prompts.append(f"{self.SLOT_MARKERS['temperature']} Have you measured your temperature? What was it?")
        if self._needs_pain_location(history, user_text) and "pain_location" not in asked and "pain_location" not in answered and "location" not in lower:
            prompts.append(f"{self.SLOT_MARKERS['pain_location']} Where exactly is the pain located?")

        if prompts:
            # Friendly preamble + join prompts
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
        # Remove slot markers from key questions text
        clean_assistant = [" ".join(part for part in a.split() if not part.startswith("[slot:")) for a in assistant_inputs]
        questions = " ".join(clean_assistant[-2:]).strip() or "No specific questions asked."
        return {
            "chief_complaint": user_inputs[0] if user_inputs else "N/A",
            "history_of_present_illness": summary,
            "key_questions": questions,
            "timestamp": datetime.utcnow().isoformat(),
        }
