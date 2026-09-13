"""
LangChain tool for computing total sales cost from Sales_item_store_history.
"""
import logging
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
DB_FILE = BASE_DIR / "mockup_db" / "vendor_agreement.db"


class TotalSalesCostInput(BaseModel):
    item_nbrs: List[int] = Field(
        ..., description="List of item numbers to include in the total sales cost calculation."
    )
    start_date: date = Field(
        ..., description="Start date (inclusive) of the sales period, format YYYY-MM-DD."
    )
    end_date: date = Field(
        ..., description="End date (inclusive) of the sales period, format YYYY-MM-DD."
    )


@tool("get_total_sales_cost", args_schema=TotalSalesCostInput)
def get_total_sales_cost(item_nbrs: List[int], start_date: date, end_date: date) -> float:
    """
    Compute the total sales cost (sales_qty * item_cost) for the given items
    between start_date and end_date (inclusive), using Sales_item_store_history.
    """
    if not item_nbrs:
        return 0.0

    placeholders = ",".join("?" for _ in item_nbrs)
    query = f"""
        SELECT COALESCE(SUM(sales_qty * item_cost), 0)
        FROM Sales_item_store_history
        WHERE item_nbr IN ({placeholders})
          AND sales_date BETWEEN ? AND ?
    """
    params = [*item_nbrs, start_date.isoformat(), end_date.isoformat()]

    conn = sqlite3.connect(DB_FILE)
    try:
        total = conn.execute(query, params).fetchone()[0]
    finally:
        conn.close()

    logger.info(
        "Computed total sales cost for %d item(s) between %s and %s: %s",
        len(item_nbrs), start_date, end_date, total,
    )

    return round(total or 0.0, 2)


class ItemLevelSalesInput(BaseModel):
    item_nbrs: List[int] = Field(
        ..., description="List of item numbers to summarize sales for."
    )
    start_date: date = Field(
        ..., description="Start date (inclusive) of the sales period, format YYYY-MM-DD."
    )
    end_date: date = Field(
        ..., description="End date (inclusive) of the sales period, format YYYY-MM-DD."
    )
    allowance_percentage: float = Field(
        ..., description="The agreement allowance percentage to apply, e.g. 5 for 5%."
    )


@tool("get_item_level_sales_summary", args_schema=ItemLevelSalesInput)
def get_item_level_sales_summary(
    item_nbrs: List[int], start_date: date, end_date: date, allowance_percentage: float
) -> List[Dict[str, Any]]:
    """
    Compute, per item and per sales date, the total sales quantity and total
    sales cost (sales_qty * item_cost) between start_date and end_date
    (inclusive), using Sales_item_store_history.

    Returns a list of records, one per item per sales date, each containing:
      - item: the item number
      - sales_date: the sales date the totals apply to
      - total_sales_qty: summed sales_qty for the item on that date
      - total_sales_cost: summed sales_qty * item_cost for the item on that date
      - allowance_amount: (allowance_percentage / 100) * total_sales_cost
    """
    if not item_nbrs:
        return []

    placeholders = ",".join("?" for _ in item_nbrs)
    query = f"""
        SELECT item_nbr,
               sales_date,
               COALESCE(SUM(sales_qty), 0) AS total_sales_qty,
               COALESCE(SUM(sales_qty * item_cost), 0) AS total_sales_cost
        FROM Sales_item_store_history
        WHERE item_nbr IN ({placeholders})
          AND sales_date BETWEEN ? AND ?
        GROUP BY item_nbr, sales_date
        ORDER BY item_nbr, sales_date
    """
    params = [*item_nbrs, start_date.isoformat(), end_date.isoformat()]

    conn = sqlite3.connect(DB_FILE)
    try:
        results = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    records = [
        {
            "item": item_nbr,
            "sales_date": sales_date,
            "total_sales_qty": total_sales_qty,
            "total_sales_cost": round(total_sales_cost or 0.0, 2),
            "allowance_amount": round((allowance_percentage / 100) * (total_sales_cost or 0.0), 2),
        }
        for item_nbr, sales_date, total_sales_qty, total_sales_cost in results
    ]

    logger.info(
        "Computed item-level sales summary for %d item(s) between %s and %s.",
        len(item_nbrs), start_date, end_date,
    )

    return records
