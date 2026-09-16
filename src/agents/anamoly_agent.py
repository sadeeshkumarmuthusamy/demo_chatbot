"""
LangChain/LangGraph agent (Groq LLM) that detects allowance anomalies for a
given vendor agreement.

The agent compares the allowance amount calculated from sales data against
the allowance amount recorded in Agreement_allowance_history, and if they
differ,drills down to item/date level to surface the anomaly.
"""
import argparse
import logging

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from src.settings.config import config
from src.tools.allownce_history import (
    calculate_allowance_amount,
    get_agreement_details,
    get_item_level_allowance_summary,
    get_total_allowance_amount,
)
from src.tools.sales_history import get_item_level_sales_summary, get_total_sales_cost

logger = logging.getLogger(__name__)

DEFAULT_MODEL = config.GROQ_LLM_MODEL

SYSTEM_PROMPT = """\
You are an anomaly-detection agent for vendor allowance agreements. Given an
agreement id, follow these steps exactly, using the available tools, and do
not skip or reorder any step:

Step 1: Call get_agreement_details with the agreement id to get the
agreement start date, end date, agreement type, allowance percent, and item
list.

Step 2: Call get_total_sales_cost with the item list and the agreement start
date/end date (from Step 1) to get the total sales cost.

Step 3: Call calculate_allowance_amount with the agreement id, the allowance
percent (from Step 1), and the total sales cost (from Step 2) to get the
calculated allowance amount.

Step 4: Call get_total_allowance_amount with the agreement id (from Step 1)
to get the recorded allowance amount from Agreement_allowance_history.

Step 5: Compare the calculated allowance amount (Step 3) with the recorded
allowance amount (Step 4).

Step 6a: If there is no meaningful difference between the two amounts, stop
here and respond with a summary containing: agreement id, total sales cost,
and allowance amount. Do not perform Steps 7-9.

Step 6: If there is a difference between the two amounts, proceed to Steps
7, 8, and 9.

Step 7: Call get_item_level_sales_summary with the item list, start date,
end date, and allowance percent (from Step 1) to get item/date level sales
and allowance details.

Step 8: Call get_item_level_allowance_summary with the agreement id to get
item/date level allowance details from Agreement_allowance_history.

Step 9: Compare the results of Step 7 and Step 8 at the item and date level,
and report the differences to the user as the anomaly, clearly listing which
items/dates are mismatched and by how much.

Always present your final answer as a clear, structured summary.
"""

TOOLS = [
    get_agreement_details,
    get_total_sales_cost,
    calculate_allowance_amount,
    get_total_allowance_amount,
    get_item_level_sales_summary,
    get_item_level_allowance_summary,
]


def build_anomaly_agent(model: str = DEFAULT_MODEL):
    """Build and return the allowance-anomaly detection agent."""
    llm = ChatGroq(model=model, api_key=config.GROQ_API_KEY, temperature=0)
    return create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT)


def run_anomaly_check(agreement_id: int) -> str:
    """Run the anomaly-detection agent for the given agreement id and return its final answer."""
    agent = build_anomaly_agent(model=DEFAULT_MODEL)
    result = agent.invoke(
        {
            "messages": [
                ("user", f"Check agreement id {agreement_id} for allowance anomalies.")
            ]
        }
    )
    return result["messages"][-1].content


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

#     parser = argparse.ArgumentParser(description="Run the allowance anomaly detection agent.")
#     parser.add_argument("agreement_id", type=int, help="Agreement id to check for anomalies.")
#     parser.add_argument("--model", default=DEFAULT_MODEL, help="Groq model to use.")
#     args = parser.parse_args()

#     print(run_anomaly_check(args.agreement_id))
