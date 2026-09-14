"""
Chatbot orchestrator agent (Groq LLM) that acts as the backend for the
Gradio chat UI.

It routes user requests to the specialized agents (allowance anomaly
detection, finance reconciliation) when the user references an agreement id
and a relevant task, and answers generic questions directly using the LLM.
All user input is first screened for PII and prompt-injection attempts via
src.agent.guardrails.
"""
import logging
from typing import List, Optional, Tuple

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.agents.guardrails import check_input
from src.agents.anamoly_agent import run_anomaly_check
from src.agents.financerecon_agent import run_financerecon_check
from src.settings.config import config

logger = logging.getLogger(__name__)

DEFAULT_MODEL = config.GROQ_LLM_MODEL


class AgreementIdInput(BaseModel):
    agreement_id: int = Field(..., description="The vendor agreement id to check.")


@tool("check_allowance_anomaly", args_schema=AgreementIdInput)
def check_allowance_anomaly(agreement_id: int) -> str:
    """
    Run the allowance anomaly detection agent for the given agreement id.
    Use this when the user asks about allowance discrepancies or anomalies,
    or whether the recorded allowance amount matches what sales data
    implies, for a specific vendor agreement.
    """
    return run_anomaly_check(agreement_id)


@tool("check_finance_reconciliation", args_schema=AgreementIdInput)
def check_finance_reconciliation(agreement_id: int) -> str:
    """
    Run the finance reconciliation agent for the given agreement id. Use
    this when the user asks about bill/invoice reconciliation, or whether
    billed amounts match SAP invoice amounts, for a specific vendor
    agreement.
    """
    return run_financerecon_check(agreement_id)


TOOLS = [check_allowance_anomaly, check_finance_reconciliation]

SYSTEM_PROMPT = """\
You are the front-line assistant for a vendor agreement management chatbot.

You have two specialized tools available:
- check_allowance_anomaly(agreement_id): checks whether the allowance
  amount recorded for a vendor agreement matches what sales data implies,
  and reports any anomalies.
- check_finance_reconciliation(agreement_id): checks whether billed amounts
  for a vendor agreement reconcile against SAP invoice amounts, and reports
  any deviations.

Routing rules:
1. If the user asks about allowance anomalies/discrepancies for a specific
   agreement and gives an agreement id, call check_allowance_anomaly with
   that agreement id.
2. If the user asks about bill/invoice reconciliation or SAP invoice
   mismatches for a specific agreement and gives an agreement id, call
   check_finance_reconciliation with that agreement id.
3. If the user's request matches one of the above but no agreement id was
   given, ask the user to provide the agreement id. Do not guess an id.
4. If the user asks a generic question unrelated to the above two tasks,
   answer it directly yourself using your own knowledge, without calling
   any tool.

Always present tool results as a clear, structured summary for the user.
"""


def build_chatbot_agent(model: str = DEFAULT_MODEL):
    """Build and return the chatbot orchestrator agent."""
    llm = ChatGroq(model=model, api_key=config.GROQ_API_KEY, temperature=0)
    return create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT)


_agent = None


def _get_agent():
    """Lazily build and cache the orchestrator agent."""
    global _agent
    if _agent is None:
        _agent = build_chatbot_agent()
    return _agent


def _history_to_messages(history: Optional[list]) -> List[Tuple[str, str]]:
    """
    Convert Gradio chat history into LangChain-style (role, content) tuples.

    Supports both the modern Gradio "messages" format (list of
    {"role": ..., "content": ...} dicts) and the legacy format (list of
    (user, assistant) tuples).
    """
    messages: List[Tuple[str, str]] = []
    if not history:
        return messages

    for entry in history:
        if isinstance(entry, dict):
            role = entry.get("role")
            content = entry.get("content")
            if role and content:
                messages.append((role, content))
        else:
            user_msg, assistant_msg = entry
            if user_msg:
                messages.append(("user", user_msg))
            if assistant_msg:
                messages.append(("assistant", assistant_msg))
    return messages


def handle_user_message(message: str, history: Optional[list] = None) -> str:
    """
    Handle a single user chat message: run guardrail checks (PII, prompt
    injection) first, then route to the orchestrator agent, which will
    either call a specialized tool (using the agreement id) or answer the
    generic question directly.
    """
    guardrail_result = check_input(message)
    if guardrail_result.is_blocked:
        reasons = "; ".join(guardrail_result.reasons)
        logger.warning("Blocked user message due to guardrail violation(s): %s", reasons)
        return (
            "I can't process that message because it appears to contain "
            f"sensitive or unsafe content ({reasons}). "
            "Please rephrase your question without sharing personal data, "
            "and avoid trying to change my instructions."
        )

    agent = _get_agent()
    messages = _history_to_messages(history)
    messages.append(("user", message))

    result = agent.invoke({"messages": messages})
    return result["messages"][-1].content


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
#     print(handle_user_message("Check agreement id 1001 for allowance anomalies."))
