"""
LangChain tools for reading bill totals from SAP_Invoice_history and
Agreement_bill_history.
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


@tool("get_sap_bill_amount_by_date", args_schema=AgreementIdInput)
def get_sap_bill_amount_by_date(agreement_id: int) -> List[Dict[str, Any]]:
    """
    Compute the total SAP_Bill_amount per SAP_Bill_date for the given
    agreement id, using SAP_Invoice_history.

    Returns a list of records, one per SAP_Bill_date, each containing:
      - SAP_Bill_amount: summed SAP_Bill_amount for that date
      - SAP_Bill_date: the date the total applies to
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        results = conn.execute(
            """
            SELECT SAP_Bill_date,
                   COALESCE(SUM(SAP_Bill_amount), 0) AS total_sap_bill_amount
            FROM SAP_Invoice_history
            WHERE Agreement_id = ?
            GROUP BY SAP_Bill_date
            ORDER BY SAP_Bill_date
            """,
            (agreement_id,),
        ).fetchall()
    finally:
        conn.close()

    records = [
        {
            "SAP_Bill_amount": round(total_sap_bill_amount or 0.0, 2),
            "SAP_Bill_date": sap_bill_date,
        }
        for sap_bill_date, total_sap_bill_amount in results
    ]

    logger.info(
        "Computed SAP bill amount by date for agreement %s: %d record(s).",
        agreement_id, len(records),
    )

    return records


@tool("get_bill_amount_by_date", args_schema=AgreementIdInput)
def get_bill_amount_by_date(agreement_id: int) -> List[Dict[str, Any]]:
    """
    Compute the total Bill_amount per Bill_date for the given agreement id,
    using Agreement_bill_history.

    Returns a list of records, one per Bill_date, each containing:
      - Bill_amount: summed Bill_amount for that date
      - Bill_date: the date the total applies to
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        results = conn.execute(
            """
            SELECT Bill_date,
                   COALESCE(SUM(Bill_amount), 0) AS total_bill_amount
            FROM Agreement_bill_history
            WHERE Agreement_id = ?
            GROUP BY Bill_date
            ORDER BY Bill_date
            """,
            (agreement_id,),
        ).fetchall()
    finally:
        conn.close()

    records = [
        {
            "Bill_amount": round(total_bill_amount or 0.0, 2),
            "Bill_date": bill_date,
        }
        for bill_date, total_bill_amount in results
    ]

    logger.info(
        "Computed bill amount by date for agreement %s: %d record(s).",
        agreement_id, len(records),
    )

    return records
