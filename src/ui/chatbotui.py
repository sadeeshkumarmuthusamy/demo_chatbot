"""
Gradio chat UI for the vendor agreement chatbot.

Run with:
    python -m src.ui.chatbotui
"""
import logging
import sys
from pathlib import Path

# Ensure the project root is importable as "src...", regardless of how this
# file is invoked (e.g. `python src/ui/chatbotui.py` or `python -m src.ui.chatbotui`).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import gradio as gr

from src.agents.chatbot_agent import handle_user_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def respond(message: str, history: list) -> str:
    """Gradio ChatInterface callback: handle a single user message."""
    try:
        return handle_user_message(message, history)
    except Exception:
        logger.exception("Error handling chat message.")
        return "Sorry, something went wrong while processing your request. Please try again."


demo = gr.ChatInterface(
    fn=respond,
    title="Vendor Agreement Assistant",
    description=(
        "Ask about allowance anomalies or bill/invoice reconciliation for a "
        "vendor agreement (include the agreement id), or ask a general "
        "question."
    ),
    examples=[
        "Check agreement id 1001 for allowance anomalies.",
        "Reconcile bill amounts for agreement id 1001.",
        "What is a vendor allowance agreement?",
    ],
)

if __name__ == "__main__":
    demo.launch()
