"""
LangChain tools for reading allowance and agreement details from
Agreement_allowance_history, Vendor, and Agreement_item.
"""
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
DB_FILE = BASE_DIR / "mockup_db" / "vendor_agreement.db"


class AgreementIdInput(BaseModel):
    agreement_id: int = Field(..., description="The agreement id to look up.")


@tool("get_total_allowance_amount", args_schema=AgreementIdInput)
def get_total_allowance_amount(agreement_id: int) -> float:
    """
    Compute the total allowance amount for the given agreement id, using
    Agreement_allowance_history.
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        total = conn.execute(
            """
            SELECT COALESCE(SUM(allowance_amount), 0)
            FROM Agreement_allowance_history
            WHERE Agreement_id = ?
            """,
            (agreement_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    logger.info("Computed total allowance amount for agreement %s: %s", agreement_id, total)

    return round(total or 0.0, 2)


@tool("get_item_level_allowance_summary", args_schema=AgreementIdInput)
def get_item_level_allowance_summary(agreement_id: int) -> List[Dict[str, Any]]:
    """
    Compute, per item and per sales date, the total allowance amount for the
    given agreement id, using Agreement_allowance_history.

    Returns a list of records, one per item per sales date, each containing:
      - item: the item number
      - total_allowance_amt: summed allowance_amount for the item on that date
      - date: the sales date the total applies to
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        results = conn.execute(
            """
            SELECT item_nbr,
                   sales_date,
                   COALESCE(SUM(allowance_amount), 0) AS total_allowance_amt
            FROM Agreement_allowance_history
            WHERE Agreement_id = ?
            GROUP BY item_nbr, sales_date
            ORDER BY item_nbr, sales_date
            """,
            (agreement_id,),
        ).fetchall()
    finally:
        conn.close()

    records = [
        {
            "item": item_nbr,
            "total_allowance_amt": round(total_allowance_amt or 0.0, 2),
            "date": sales_date,
        }
        for item_nbr, sales_date, total_allowance_amt in results
    ]

    logger.info(
        "Computed item-level allowance summary for agreement %s: %d record(s).",
        agreement_id, len(records),
    )

    return records


@tool("get_agreement_details", args_schema=AgreementIdInput)
def get_agreement_details(agreement_id: int) -> Dict[str, Any]:
    """
    Get the agreement start date, end date, agreement type, allowance percent,
    and the list of items covered, using Vendor and Agreement_item.
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        vendor_row = conn.execute(
            """
            SELECT Agreement_start_date, Agreement_end_date, Agreement_type,
                   Agreement_allowance_percent
            FROM Vendor
            WHERE Agreement_id = ?
            """,
            (agreement_id,),
        ).fetchone()

        item_rows = conn.execute(
            """
            SELECT item_nbr
            FROM Agreement_item
            WHERE Agreement_id = ?
            ORDER BY item_nbr
            """,
            (agreement_id,),
        ).fetchall()
    finally:
        conn.close()

    if vendor_row is None:
        logger.info("No agreement found for agreement %s.", agreement_id)
        return {}

    start_date, end_date, agreement_type, allowance_percent = vendor_row
    item_list = [item_nbr for (item_nbr,) in item_rows]

    logger.info(
        "Retrieved agreement details for agreement %s: %d item(s).",
        agreement_id, len(item_list),
    )

    return {
        "agreement_start_date": start_date,
        "agreement_end_date": end_date,
        "agreement_type": agreement_type,
        "allowance_percent": allowance_percent,
        "item_list": item_list,
    }


class CalculateAllowanceAmountInput(BaseModel):
    agreement_id: int = Field(..., description="The agreement id the calculation is for.")
    allowance_percentage: float = Field(
        ..., description="The allowance percentage to apply, e.g. 5 for 5%."
    )
    total_sales_cost: float = Field(
        ..., description="The total sales cost to apply the allowance percentage to."
    )


@tool("calculate_allowance_amount", args_schema=CalculateAllowanceAmountInput)
def calculate_allowance_amount(
    agreement_id: int, allowance_percentage: float, total_sales_cost: float
) -> float:
    """
    Calculate the allowance amount for an agreement as
    total_sales_cost * (allowance_percentage / 100).
    """
    allowance_amount = total_sales_cost * (allowance_percentage / 100)

    logger.info(
        "Calculated allowance amount for agreement %s: %s (percentage=%s, total_sales_cost=%s)",
        agreement_id, allowance_amount, allowance_percentage, total_sales_cost,
    )

    return round(allowance_amount, 2)