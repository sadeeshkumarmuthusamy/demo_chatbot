"""
Lightweight input guardrails for the chatbot: PII detection and
prompt-injection detection, run on raw user input before it is passed to
any LLM or agent.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

# --- PII detection -------------------------------------------------------

_PII_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "phone_number": re.compile(r"\b(?:\+?\d{1,2}[ -]?)?(?:\(\d{3}\)|\d{3})[ -]?\d{3}[ -]?\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


def detect_pii(text: str) -> List[str]:
    """Return a list of PII categories detected in text (empty if none found)."""
    found = [label for label, pattern in _PII_PATTERNS.items() if pattern.search(text)]
    if found:
        logger.warning("Detected potential PII in user input: %s", found)
    return found


# --- Prompt-injection detection ------------------------------------------

_PROMPT_INJECTION_PHRASES = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the above",
    "disregard previous instructions",
    "disregard the system prompt",
    "forget previous instructions",
    "forget all previous instructions",
    "you are no longer",
    "reveal your system prompt",
    "reveal your instructions",
    "show me your system prompt",
    "what is your system prompt",
    "pretend you are",
    "jailbreak",
    "developer mode",
    "do anything now",
    "dan mode",
    "bypass your instructions",
    "override your instructions",
    "print your prompt",
    "repeat the words above",
    "act as if you have no restrictions",
]

_PROMPT_INJECTION_PATTERN = re.compile(
    "|".join(re.escape(phrase) for phrase in _PROMPT_INJECTION_PHRASES), re.IGNORECASE
)


def detect_prompt_injection(text: str) -> bool:
    """Return True if text looks like a prompt-injection attempt."""
    match = _PROMPT_INJECTION_PATTERN.search(text)
    if match:
        logger.warning("Detected potential prompt injection in user input: %r", match.group(0))
        return True
    return False


@dataclass
class GuardrailResult:
    is_blocked: bool
    reasons: List[str] = field(default_factory=list)


def check_input(text: str) -> GuardrailResult:
    """Run all guardrail checks on the given text and return the combined result."""
    reasons = []

    pii_found = detect_pii(text)
    if pii_found:
        reasons.append(f"potential PII detected ({', '.join(pii_found)})")

    if detect_prompt_injection(text):
        reasons.append("potential prompt injection attempt detected")

    return GuardrailResult(is_blocked=bool(reasons), reasons=reasons)
