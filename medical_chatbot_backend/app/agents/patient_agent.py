from typing import Dict, List, Set, Tuple
from datetime import datetime
from ..models.schemas import Message

class PatientAgent:
    """
    PatientAgent handles conversational structure, gathers symptoms interactively,
    and produces succinct structured notes.

    Strategy to avoid repetition:
    - Maintain explicit session-state sets for ASKED and ANSWERED slots carried by ChatService.
    - Continue to infer answers from user text heuristically.
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
        self.BASE_SLOTS = ("duration", "severity", "associated")

    def _asked_slots_from_history(self, history: List[Message]) -> Set[str]:
        asked: Set[str] = set()
        for m in history:
            if m.role != "assistant":
                continue
            text = (m.content or "").lower()
            for slot, token in self.SLOT_MARKERS.items():
                if token in text:
                    asked.add(slot)
        return asked

    def _answered_slots_from_history(self, history: List[Message]) -> Set[str]:
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
        if "temperature" in text or any(k in text for k in ["°c", "°f", "fever of", "temp", "measured my temperature", "my temp"]):
            answered.add("temperature")
        if any(k in text for k in ["pain in", "hurts in", "located", "location", "at my", "on my", "my pain is in"]):
            answered.add("pain_location")

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

    def _triage_complete(self, asked: Set[str], answered: Set[str], needs_temp: bool, needs_pain_loc: bool) -> bool:
        # All base slots answered
        base_ok = all(s in answered for s in self.BASE_SLOTS)
        temp_ok = (not needs_temp) or ("temperature" in answered)
        pain_ok = (not needs_pain_loc) or ("pain_location" in answered)
        return base_ok and temp_ok and pain_ok

    # PUBLIC_INTERFACE
    def respond(
        self,
        history: List[Message],
        user_text: str,
        asked_slots: Set[str] = None,
        answered_slots: Set[str] = None,
    ) -> Tuple[str, Dict[str, object]]:
        """
        Generate a conversational response to collect details.
        Avoids repeating prior questions by using explicit asked/answered sets provided by the caller
        (ChatService session memory) combined with inference from history.

        Returns:
            (assistant_text, state_dict)
            state_dict contains updated 'asked_slots', 'answered_slots', and 'triage_complete' boolean.
        """
        lower = (user_text or "").lower()
        prompts: List[str] = []

        # Merge explicit state with inferred history
        explicit_asked = asked_slots or set()
        explicit_answered = answered_slots or set()
        inferred_asked = self._asked_slots_from_history(history)
        inferred_answered = self._answered_slots_from_history(history)

        asked = set(explicit_asked) | set(inferred_asked)
        answered = set(explicit_answered) | set(inferred_answered)

        # Conditional needs
        needs_temp = self._needs_temperature(history, user_text)
        needs_pain_loc = self._needs_pain_location(history, user_text)

        # Base slots: duration, severity, associated
        if "duration" not in asked and "duration" not in answered:
            prompts.append(f"{self.SLOT_MARKERS['duration']} How long have you had these symptoms?")
            asked.add("duration")
        if "severity" not in asked and "severity" not in answered:
            prompts.append(f"{self.SLOT_MARKERS['severity']} How severe are they (mild/moderate/severe or 1-10)?")
            asked.add("severity")
        if "associated" not in asked and "associated" not in answered:
            prompts.append(f"{self.SLOT_MARKERS['associated']} Any other associated symptoms?")
            asked.add("associated")

        # Conditional slots
        if needs_temp and "temperature" not in asked and "temperature" not in answered and "temperature" not in lower:
            prompts.append(f"{self.SLOT_MARKERS['temperature']} Have you measured your temperature? What was it?")
            asked.add("temperature")
        if needs_pain_loc and "pain_location" not in asked and "pain_location" not in answered and "location" not in lower:
            prompts.append(f"{self.SLOT_MARKERS['pain_location']} Where exactly is the pain located?")
            asked.add("pain_location")

        triage_done = self._triage_complete(answered=answered, asked=asked, needs_temp=needs_temp, needs_pain_loc=needs_pain_loc)

        if prompts:
            # Friendly preamble + join prompts
            text_out = "Thanks for the details. " + " ".join(prompts)
        else:
            text_out = (
                "Thank you. I will summarize and provide general guidance. "
                "Please remember: this is not medical advice."
            )

        state = {
            "asked_slots": asked,
            "answered_slots": answered,
            "triage_complete": triage_done,
        }
        return text_out, state

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
