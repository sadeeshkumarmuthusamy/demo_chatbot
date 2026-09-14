"""
Loads mock sample data into the Vendor and Agreement_item tables:
- 10 sample agreements (Vendor table)
- 10 items per agreement (Agreement_item table)
"""

import logging
import random
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from DB_schema import DB_FILE, create_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

VENDOR_NAMES = [
    "Acme Supplies",
    "Global Foods Inc",
    "Northwind Distributors",
    "Sunrise Beverages",
    "Prime Produce Co",
    "Coastal Seafood Ltd",
    "Everest Dairy",
    "Harvest Grains",
    "Bluebird Bakery",
    "Cascade Cleaning Co",
]

AGREEMENT_STATUSES = [1, 2, 3]          # e.g. 1=Active, 2=Pending, 3=Closed
DIVISIONS = [10, 20, 30]                # sample division codes
ALLOWANCE_TYPES = ["OI", "BD", "MK", "SC"]
FREQUENCIES = ["M", "W", "Q"]           # Monthly, Weekly, Quarterly
AGREEMENT_TYPES = ["SALE", "RECV"]      # SALE = Sales agreement, RECV = Receivings agreement

ALLOWANCE_HISTORY_START_DATE = date(2026, 8, 11)
ALLOWANCE_TRANSACTIONS_PER_ITEM = 30
STORE_NUMBERS = list(range(101, 121))   # sample store numbers
DEPT_NUMBERS = list(range(10, 30))      # sample department numbers
BILLS_PER_AGREEMENT = 5
SEQ_NBRS_PER_BILL = ALLOWANCE_TRANSACTIONS_PER_ITEM // BILLS_PER_AGREEMENT


def load_vendors(conn: sqlite3.Connection, num_agreements: int = 10) -> list[tuple[int, int]]:
    """Insert sample agreements into the Vendor table. Returns list of (agreement_id, vendor_id)."""
    agreement_ids: list[tuple[int, int]] = []
    today = date.today()

    rows = []
    for i in range(num_agreements):
        agreement_id = 1000 + i + 1
        vendor_id = 500 + i + 1
        agreement_type = random.choice(AGREEMENT_TYPES)
        vendor_name = VENDOR_NAMES[i % len(VENDOR_NAMES)]
        start_date = today - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(180, 730))
        status = random.choice(AGREEMENT_STATUSES)
        division = random.choice(DIVISIONS)
        allowance_type = random.choice(ALLOWANCE_TYPES)
        allowance_percent = round(random.uniform(1.0, 25.0), 2)
        bill_frequency = random.choice(FREQUENCIES)
        store_alloc_frequency = random.choice(FREQUENCIES)
        last_updated_timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
        last_change_userid = "MOCKLOAD"

        rows.append((
            agreement_id,
            vendor_id,
            agreement_type,
            vendor_name,
            start_date.isoformat(),
            end_date.isoformat(),
            status,
            division,
            allowance_type,
            allowance_percent,
            bill_frequency,
            store_alloc_frequency,
            last_updated_timestamp,
            last_change_userid,
        ))
        agreement_ids.append((agreement_id, vendor_id))

    conn.executemany(
        """
        INSERT INTO Vendor (
            Agreement_id, Vendor_id, Agreement_type, Vendor_Name,
            Agreement_start_date, Agreement_end_date, Agreement_status,
            agreement_division, Agreement_allowance_type, Agreement_allowance_percent,
            Bill_frequency, Store_alloc_frequency,
            Last_updated_timestamp, Last_change_userid
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d agreements into Vendor.", len(rows))
    return agreement_ids


def load_agreement_items(
    conn: sqlite3.Connection,
    agreement_ids: list[tuple[int, int]],
    items_per_agreement: int = 10,
) -> None:
    """Insert sample items for each agreement into the Agreement_item table."""
    rows = []
    for agreement_id, vendor_id in agreement_ids:
        for j in range(items_per_agreement):
            item_nbr = agreement_id * 100 + j + 1
            item_desc = f"Sample item {j + 1} for agreement {agreement_id}"
            rows.append((agreement_id, vendor_id, item_nbr, item_desc))

    conn.executemany(
        """
        INSERT INTO Agreement_item (Agreement_id, Vendor_id, item_nbr, item_desc)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d items into Agreement_item.", len(rows))


def load_allowance_history(conn: sqlite3.Connection) -> None:
    """
    For every agreement in Vendor and every item tied to that agreement in
    Agreement_item, create ALLOWANCE_TRANSACTIONS_PER_ITEM daily transactions
    in Agreement_allowance_history, starting at ALLOWANCE_HISTORY_START_DATE.

    allowance_amount = (item_cost * quantity) * (Agreement_allowance_percent / 100)
    where Agreement_allowance_percent is looked up per agreement from Vendor.
    """
    vendors = conn.execute(
        "SELECT Agreement_id, Vendor_id, Agreement_allowance_type, Agreement_allowance_percent "
        "FROM Vendor"
    ).fetchall()
    vendor_lookup = {
        (agreement_id, vendor_id): (allowance_type, allowance_percent)
        for agreement_id, vendor_id, allowance_type, allowance_percent in vendors
    }

    items = conn.execute(
        "SELECT Agreement_id, Vendor_id, item_nbr FROM Agreement_item"
    ).fetchall()

    rows = []
    for agreement_id, vendor_id, item_nbr in items:
        allowance_type, allowance_percent = vendor_lookup[(agreement_id, vendor_id)]
        allowance_percent = allowance_percent or 0

        for seq_nbr in range(1, ALLOWANCE_TRANSACTIONS_PER_ITEM + 1):
            sales_date = ALLOWANCE_HISTORY_START_DATE + timedelta(days=seq_nbr - 1)
            process_date = sales_date
            purchase_order_id = item_nbr * 1000 + seq_nbr
            store_nbr = random.choice(STORE_NUMBERS)
            dept_nbr = random.choice(DEPT_NUMBERS)
            item_cost = round(random.uniform(5.0, 500.0), 2)
            quantity = random.randint(1, 100)
            canculated_amt = round(item_cost * quantity, 2)
            allowance_amount = round(canculated_amt * (allowance_percent / 100), 2)
            last_change_timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

            rows.append((
                agreement_id,
                vendor_id,
                purchase_order_id,
                sales_date.isoformat(),
                item_nbr,
                store_nbr,
                process_date.isoformat(),
                seq_nbr,
                item_cost,
                allowance_type,
                dept_nbr,
                quantity,
                canculated_amt,
                allowance_amount,
                None,               # bill_nbr
                None,               # Bill_date
                "Y",                # Store_Alloc_ind
                sales_date.isoformat(),  # Store_Alloc_date
                "MOCKLOAD",         # Last_change_user_id
                last_change_timestamp,
            ))

    conn.executemany(
        """
        INSERT INTO Agreement_allowance_history (
            Agreement_id, Vendor_id, purchase_order_id, sales_date,
            item_nbr, store_nbr, process_date, seq_nbr,
            item_cost, Agreement_allowance_type, dept_nbr, quantity,
            canculated_amt, allowance_amount, bill_nbr, Bill_date,
            Store_Alloc_ind, Store_Alloc_date,
            Last_change_user_id, Last_change_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d rows into Agreement_allowance_history.", len(rows))


def load_bill_history(conn: sqlite3.Connection) -> None:
    """
    Create BILLS_PER_AGREEMENT bills per agreement in Agreement_bill_history.
    Each Agreement_allowance_history transaction is assigned to one of those
    bills (grouped by seq_nbr bucket), and the bill's Bill_amount is set to
    the sum of allowance_amount for the transactions assigned to it. Vendor_id
    is carried over from Vendor so it matches across both tables.
    """
    agreements = conn.execute("SELECT Agreement_id, Vendor_id FROM Vendor").fetchall()

    bill_rows = []
    allowance_updates = []

    for agreement_id, vendor_id in agreements:
        allowance_rows = conn.execute(
            """
            SELECT purchase_order_id, sales_date, item_nbr, store_nbr,
                   process_date, seq_nbr, allowance_amount
            FROM Agreement_allowance_history
            WHERE Agreement_id = ? AND Vendor_id = ?
            """,
            (agreement_id, vendor_id),
        ).fetchall()

        buckets: dict[int, list] = {i: [] for i in range(BILLS_PER_AGREEMENT)}
        for purchase_order_id, sales_date, item_nbr, store_nbr, process_date, seq_nbr, allowance_amount in allowance_rows:
            bucket_index = min((seq_nbr - 1) // SEQ_NBRS_PER_BILL, BILLS_PER_AGREEMENT - 1)
            buckets[bucket_index].append(
                (purchase_order_id, sales_date, item_nbr, store_nbr, process_date, allowance_amount)
            )

        for bucket_index, bucket_rows in buckets.items():
            bill_nbr = agreement_id * 10 + bucket_index + 1
            bill_date = ALLOWANCE_HISTORY_START_DATE + timedelta(
                days=(bucket_index + 1) * SEQ_NBRS_PER_BILL - 1
            )
            bill_amount = round(sum(row[5] for row in bucket_rows), 2)
            transacion_id = uuid.uuid4().hex[:20]
            sap_doc_nbr = uuid.uuid4().hex[:20]
            bill_credit_account = random.randint(100000, 199999)
            bill_debit_account = random.randint(200000, 299999)
            posting_timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

            bill_rows.append((
                agreement_id,
                vendor_id,
                bill_nbr,
                bill_date.isoformat(),
                transacion_id,
                bill_amount,
                bill_credit_account,   # Bill_credit_account
                bill_debit_account,    # Bill_debit_account
                sap_doc_nbr,           # sap_doc_nbr
                0,                  # posting_response_code
                posting_timestamp,
                "MOCKLOAD",         # last_changed_user_id
            ))

            for purchase_order_id, sales_date, item_nbr, store_nbr, process_date, _ in bucket_rows:
                allowance_updates.append((
                    bill_nbr,
                    bill_date.isoformat(),
                    agreement_id,
                    vendor_id,
                    purchase_order_id,
                    sales_date,
                    item_nbr,
                    store_nbr,
                    process_date,
                ))

    conn.executemany(
        """
        INSERT INTO Agreement_bill_history (
            Agreement_id, Vendor_id, Bill_nbr, Bill_date, transacion_id,
            Bill_amount, Bill_credit_account, Bill_debit_account, sap_doc_nbr,
            posting_response_code, posting_timestamp, last_changed_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        bill_rows,
    )
    logger.info("Inserted %d rows into Agreement_bill_history.", len(bill_rows))

    conn.executemany(
        """
        UPDATE Agreement_allowance_history
        SET bill_nbr = ?, Bill_date = ?
        WHERE Agreement_id = ? AND Vendor_id = ? AND purchase_order_id = ?
          AND sales_date = ? AND item_nbr = ? AND store_nbr = ? AND process_date = ?
        """,
        allowance_updates,
    )
    logger.info("Updated bill_nbr on %d Agreement_allowance_history rows.", len(allowance_updates))


def load_sap_invoice_history(conn: sqlite3.Connection) -> None:
    """
    Create one SAP_Invoice_history entry per Agreement_bill_history row.
    The document number (SAP_Bill_document_nbr) matches the bill's
    sap_doc_nbr, SAP_Bill_nbr matches Bill_nbr, and the amount/dates match
    the bill's Bill_amount/Bill_date exactly.
    """
    bill_rows = conn.execute(
        """
        SELECT Agreement_id, Bill_nbr, sap_doc_nbr, Bill_date, Bill_amount,
               Bill_credit_account, Bill_debit_account, posting_timestamp
        FROM Agreement_bill_history
        """
    ).fetchall()

    rows = []
    for agreement_id, bill_nbr, sap_doc_nbr, bill_date, bill_amount, bill_credit_account, bill_debit_account, posting_timestamp in bill_rows:
        rows.append((
            agreement_id,
            bill_nbr,
            sap_doc_nbr,
            bill_date,
            bill_date,
            1,                      # sequence_nbr
            bill_amount,
            bill_amount,            # SAP_Bill_credit_amt
            bill_amount,            # SAP_Bill_debit_amt
            bill_credit_account,    # SAP_Bill_customer_account
            bill_debit_account,     # SAP_Bill_company_amount
            posting_timestamp,
        ))

    conn.executemany(
        """
        INSERT INTO SAP_Invoice_history (
            Agreement_id, SAP_Bill_nbr, SAP_Bill_document_nbr, SAP_Bill_date, Transaction_Date,
            sequence_nbr, SAP_Bill_amount, SAP_Bill_credit_amt, SAP_Bill_debit_amt,
            SAP_Bill_customer_account, SAP_Bill_company_amount, Transaction_Timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d rows into SAP_Invoice_history.", len(rows))


def load_sap_journal_history(conn: sqlite3.Connection) -> None:
    """
    Create one SAP_Journal_history entry per Agreement_journal_history row.
    The document number (SAP_Journal_document_nbr) matches the journal's
    transacion_id, and the amount/dates match the journal's
    Journal_amount/Jorunal_date exactly.
    """
    journal_rows = conn.execute(
        """
        SELECT Vendor_id, Journal_store, Jorunal_date, Journal_amount,
               Journal_credit_account, Journal_debit_account, transacion_id
        FROM Agreement_journal_history
        """
    ).fetchall()

    rows = []
    for vendor_id, journal_store, jorunal_date, journal_amount, journal_credit_account, journal_debit_account, transacion_id in journal_rows:
        sap_journal_credit_store = str(journal_store)
        sap_journal_debit_store = str(vendor_id)
        transaction_timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

        rows.append((
            transacion_id,
            sap_journal_credit_store,
            sap_journal_debit_store,
            jorunal_date,
            jorunal_date,
            journal_amount,
            journal_amount,            # SAP_Journal_credit_amt
            journal_amount,            # SAP_Journal_debit_amt
            journal_credit_account,    # SAP_journal_credit_account
            journal_debit_account,     # SAP_journal_debit_amount
            transaction_timestamp,
        ))

    conn.executemany(
        """
        INSERT INTO SAP_Journal_history (
            SAP_Journal_document_nbr, SAP_Journal_credit_store, SAP_Journal_debit_store,
            SAP_journal_date, Transaction_Date, SAP_Journal_amount,
            SAP_Journal_credit_amt, SAP_Journal_debit_amt,
            SAP_journal_credit_account, SAP_journal_debit_amount, Transaction_Timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d rows into SAP_Journal_history.", len(rows))


def load_sales_item_store_history(conn: sqlite3.Connection) -> None:
    """
    For every SALE agreement (Vendor.Agreement_type = 'SALE'), create a
    matching Sales_item_store_history entry for each Agreement_allowance_history
    row: item_nbr, item_vendor, store_nbr, sales_date, and quantity/sales_qty
    line up between the two tables. item_cost is copied over as well.
    """
    allowance_rows = conn.execute(
        """
        SELECT a.Agreement_id, a.Vendor_id, a.item_nbr, a.store_nbr,
               a.sales_date, a.seq_nbr, a.dept_nbr, a.quantity, a.purchase_order_id,
               a.item_cost
        FROM Agreement_allowance_history a
        JOIN Vendor v ON v.Agreement_id = a.Agreement_id AND v.Vendor_id = a.Vendor_id
        WHERE v.Agreement_type = 'SALE'
        """
    ).fetchall()

    rows = []
    for agreement_id, vendor_id, item_nbr, store_nbr, sales_date, seq_nbr, dept_nbr, quantity, purchase_order_id, item_cost in allowance_rows:
        sale_unique_id = f"{purchase_order_id}-{seq_nbr}"
        item_vendor = str(vendor_id)
        item_department = str(dept_nbr)

        rows.append((
            sale_unique_id,
            item_nbr,
            item_vendor,
            item_department,
            store_nbr,
            sales_date,
            seq_nbr,
            None,               # item_category
            quantity,
            item_cost,
        ))

    conn.executemany(
        """
        INSERT INTO Sales_item_store_history (
            sale_unique_id, item_nbr, item_vendor, item_department,
            store_nbr, sales_date, sequence_nbr, item_category, sales_qty,
            item_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d rows into Sales_item_store_history.", len(rows))


def load_receivings_item_warehouse_history(conn: sqlite3.Connection) -> None:
    """
    For every RECV agreement (Vendor.Agreement_type = 'RECV'), create a
    matching Receivings_item_warehouse_history entry for each
    Agreement_allowance_history row: purchase_order_id, item_nbr, item_vendor,
    and quantity line up exactly, and the allowance store_nbr maps to
    warehouse_nbr.
    """
    allowance_rows = conn.execute(
        """
        SELECT a.purchase_order_id, a.Vendor_id, a.dept_nbr, a.item_nbr,
               a.store_nbr, a.sales_date, a.seq_nbr, a.quantity
        FROM Agreement_allowance_history a
        JOIN Vendor v ON v.Agreement_id = a.Agreement_id AND v.Vendor_id = a.Vendor_id
        WHERE v.Agreement_type = 'RECV'
        """
    ).fetchall()

    rows = []
    for purchase_order_id, vendor_id, dept_nbr, item_nbr, store_nbr, sales_date, seq_nbr, quantity in allowance_rows:
        item_vendor = str(vendor_id)
        department = str(dept_nbr)
        warehouse_nbr = str(store_nbr)
        update_timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

        rows.append((
            purchase_order_id,
            item_vendor,
            department,
            item_nbr,
            warehouse_nbr,
            sales_date,
            seq_nbr,
            quantity,           # order_qty
            quantity,           # received_qty
            update_timestamp,
        ))

    conn.executemany(
        """
        INSERT INTO Receivings_item_warehouse_history (
            purchase_order_id, item_vendor, department, item_nbr,
            warehouse_nbr, receipt_date, receiving_seq_nbr,
            order_qty, received_qty, update_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d rows into Receivings_item_warehouse_history.", len(rows))


def load_journal_history(conn: sqlite3.Connection) -> None:
    """
    Generate one Agreement_journal_history entry per Agreement_allowance_history
    row, carrying over the same amount (allowance_amount), date (sales_date),
    agreement, dept, and store (Journal_store = allowance store_nbr). A random
    transacion_id is generated for each entry.
    """
    allowance_rows = conn.execute(
        "SELECT Agreement_id, Vendor_id, sales_date, dept_nbr, store_nbr, allowance_amount "
        "FROM Agreement_allowance_history"
    ).fetchall()

    rows = []
    for agreement_id, vendor_id, sales_date, dept_nbr, store_nbr, allowance_amount in allowance_rows:
        transacion_id = uuid.uuid4().hex[:20]
        posting_timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")

        rows.append((
            agreement_id,
            sales_date,
            dept_nbr,
            store_nbr,
            transacion_id,
            vendor_id,
            allowance_amount,
            None,               # Journal_credit_account
            None,               # Journal_debit_account
            0,                  # posting_response_code
            posting_timestamp,
            "MOCKLOAD",         # last_changed_iser_id
        ))

    conn.executemany(
        """
        INSERT INTO Agreement_journal_history (
            Agreement_id, Jorunal_date, dept_nbr, Journal_store, transacion_id,
            Vendor_id, Journal_amount, Journal_credit_account, Journal_debit_account,
            posting_response_code, posting_timestamp, last_changed_iser_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("Inserted %d rows into Agreement_journal_history.", len(rows))


def main(db_file: Path = DB_FILE) -> None:
    if not db_file.exists():
        create_database(db_file)

    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        agreement_ids = load_vendors(conn)
        load_agreement_items(conn, agreement_ids)
        load_allowance_history(conn)
        load_bill_history(conn)
        load_sap_invoice_history(conn)
        load_sales_item_store_history(conn)
        load_receivings_item_warehouse_history(conn)
        load_journal_history(conn)
        load_sap_journal_history(conn)
        conn.commit()
    finally:
        conn.close()

    logger.info("Mock data load complete.")


if __name__ == "__main__":
    main()
