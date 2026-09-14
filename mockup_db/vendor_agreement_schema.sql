PRAGMA foreign_keys = ON;

-- =========================================================
-- Vendor: master agreement/vendor table
-- =========================================================
CREATE TABLE IF NOT EXISTS Vendor (
    Agreement_id                INTEGER       NOT NULL,
    Vendor_id                   INTEGER       NOT NULL,
    Agreement_type               CHAR(04),
    Vendor_Name                 CHAR(100),
    Agreement_start_date        DATE,
    Agreement_end_date          DATE,
    Agreement_status            INTEGER,
    agreement_division          SMALLINT,
    Agreement_allowance_type    CHAR(02),
    Agreement_allowance_percent DECIMAL(5,2),
    Bill_frequency               CHAR(01),
    Store_alloc_frequency        CHAR(01),
    Last_updated_timestamp       TIMESTAMP,
    Last_change_userid            CHAR(20),
    PRIMARY KEY (Agreement_id)
);

-- =========================================================
-- Agreement_item: items covered under an agreement
-- =========================================================
CREATE TABLE IF NOT EXISTS Agreement_item (
    Agreement_id INTEGER NOT NULL,
    Vendor_id    INTEGER NOT NULL,
    item_nbr     INTEGER NOT NULL,
    item_desc    CHAR(200),
    PRIMARY KEY (Agreement_id, Vendor_id, item_nbr),
    FOREIGN KEY (Agreement_id) REFERENCES Vendor (Agreement_id)
);

-- =========================================================
-- Agreement_allowance_history
-- =========================================================
CREATE TABLE IF NOT EXISTS Agreement_allowance_history (
    Agreement_id             INTEGER       NOT NULL,
    Vendor_id                INTEGER       NOT NULL,
    purchase_order_id        BIGINT        NOT NULL,
    sales_date                DATE          NOT NULL,
    item_nbr                  INTEGER       NOT NULL,
    store_nbr                 INTEGER       NOT NULL,
    process_date              DATE          NOT NULL,
    seq_nbr                   INTEGER       NOT NULL,
    item_cost                 DECIMAL(12,2),
    Agreement_allowance_type  CHAR(02),
    dept_nbr                  INTEGER,
    quantity                  INTEGER,
    canculated_amt            DECIMAL(12,2),
    allowance_amount          DECIMAL(12,2),
    bill_nbr                  INTEGER,
    Bill_date                 DATE,
    Store_Alloc_ind           CHAR(1),
    Store_Alloc_date          DATE,
    Last_change_user_id       CHAR(20),
    Last_change_timestamp     TIMESTAMP,
    PRIMARY KEY (
        Agreement_id, Vendor_id, purchase_order_id, sales_date,
        item_nbr, store_nbr, process_date, seq_nbr
    ),
    FOREIGN KEY (Agreement_id) REFERENCES Vendor (Agreement_id),
    FOREIGN KEY (Agreement_id, Vendor_id, item_nbr)
        REFERENCES Agreement_item (Agreement_id, Vendor_id, item_nbr)
);

-- =========================================================
-- Agreement_bill_history
-- =========================================================
CREATE TABLE IF NOT EXISTS Agreement_bill_history (
    Agreement_id           INTEGER NOT NULL,
    Vendor_id              INTEGER NOT NULL,
    Bill_nbr               INTEGER  NOT NULL,
    Bill_date              DATE     NOT NULL,
    transacion_id          CHAR(20) NOT NULL,
    Bill_amount            DECIMAL(14,2),
    Bill_credit_account    INTEGER,
    Bill_debit_account     INTEGER,
    sap_doc_nbr            CHAR(20),
    posting_response_code  INTEGER,
    posting_timestamp      TIMESTAMP,
    last_changed_user_id   CHAR(20),
    PRIMARY KEY (Agreement_id, Vendor_id, Bill_nbr, Bill_date, transacion_id),
    FOREIGN KEY (Agreement_id) REFERENCES Vendor (Agreement_id)
);

-- =========================================================
-- Agreement_journal_history
-- =========================================================
CREATE TABLE IF NOT EXISTS Agreement_journal_history (
    Agreement_id            INTEGER  NOT NULL,
    Jorunal_date            DATE     NOT NULL,
    dept_nbr                INTEGER  NOT NULL,
    Journal_store           INTEGER  NOT NULL,
    transacion_id           CHAR(20) NOT NULL,
    Vendor_id               INTEGER,
    Journal_amount          DECIMAL(14,2),
    Journal_credit_account  INTEGER,
    Journal_debit_account   INTEGER,
    posting_response_code   INTEGER,
    posting_timestamp       TIMESTAMP,
    last_changed_iser_id    CHAR(20),
    PRIMARY KEY (Agreement_id, Jorunal_date, dept_nbr, Journal_store, transacion_id),
    FOREIGN KEY (Agreement_id) REFERENCES Vendor (Agreement_id)
);

-- =========================================================
-- SAP_Invoice_history
-- =========================================================
CREATE TABLE IF NOT EXISTS SAP_Invoice_history (
    Agreement_id               INTEGER,
    SAP_Bill_nbr               INTEGER       NOT NULL,
    SAP_Bill_document_nbr      CHAR(20)      NOT NULL,
    SAP_Bill_date              DATE          NOT NULL,
    Transaction_Date           DATE          NOT NULL,
    sequence_nbr               INTEGER       NOT NULL,
    SAP_Bill_amount            DECIMAL(14,2),
    SAP_Bill_credit_amt        DECIMAL(14,2),
    SAP_Bill_debit_amt         DECIMAL(14,2),
    SAP_Bill_customer_account  INTEGER,
    SAP_Bill_company_amount    INTEGER,
    Transaction_Timestamp      TIMESTAMP,
    PRIMARY KEY (SAP_Bill_nbr, SAP_Bill_document_nbr, SAP_Bill_date, Transaction_Date, sequence_nbr),
    FOREIGN KEY (Agreement_id) REFERENCES Vendor (Agreement_id)
);

-- =========================================================
-- SAP_Journal_history
-- =========================================================
CREATE TABLE IF NOT EXISTS SAP_Journal_history (
    SAP_Journal_document_nbr    CHAR(20)      NOT NULL,
    SAP_Journal_credit_store    CHAR(10)      NOT NULL,
    SAP_Journal_debit_store     CHAR(10)      NOT NULL,
    SAP_journal_date            DATE          NOT NULL,
    Transaction_Date            DATE          NOT NULL,
    SAP_Journal_amount          DECIMAL(14,2),
    SAP_Journal_credit_amt      DECIMAL(14,2),
    SAP_Journal_debit_amt       DECIMAL(14,2),
    SAP_journal_credit_account  INTEGER,
    SAP_journal_debit_amount    DECIMAL(14,2),
    Transaction_Timestamp       TIMESTAMP,
    PRIMARY KEY (
        SAP_Journal_document_nbr, SAP_Journal_credit_store,
        SAP_Journal_debit_store, SAP_journal_date, Transaction_Date
    )
);

-- =========================================================
-- Sales_item_store_history
-- =========================================================
CREATE TABLE IF NOT EXISTS Sales_item_store_history (
    sale_unique_id    CHAR(30) NOT NULL,
    item_nbr          INTEGER  NOT NULL,
    item_vendor       CHAR(10) NOT NULL,
    item_department   CHAR(10) NOT NULL,
    store_nbr         INTEGER  NOT NULL,
    sales_date        DATE     NOT NULL,
    sequence_nbr      INTEGER  NOT NULL,
    item_category     CHAR(20),
    sales_qty         INTEGER,
    item_cost         DECIMAL(12,2),
    PRIMARY KEY (
        sale_unique_id, item_nbr, item_vendor, item_department,
        store_nbr, sales_date, sequence_nbr
    )
);

-- =========================================================
-- Receivings_item_warehouse_history
-- =========================================================
CREATE TABLE IF NOT EXISTS Receivings_item_warehouse_history (
    purchase_order_id   BIGINT   NOT NULL,
    item_vendor         CHAR(10) NOT NULL,
    department          CHAR(10) NOT NULL,
    item_nbr            INTEGER  NOT NULL,
    warehouse_nbr       CHAR(10) NOT NULL,
    receipt_date        DATE     NOT NULL,
    receiving_seq_nbr   INTEGER  NOT NULL,
    order_qty           INTEGER,
    received_qty        INTEGER,
    update_timestamp    TIMESTAMP,
    PRIMARY KEY (
        purchase_order_id, item_vendor, department, item_nbr,
        warehouse_nbr, receipt_date, receiving_seq_nbr
    )
);

-- =========================================================
-- Helpful secondary indexes
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_vendor_vendor_id
    ON Vendor (Vendor_id);

CREATE INDEX IF NOT EXISTS idx_agreement_item_item_nbr
    ON Agreement_item (item_nbr);

CREATE INDEX IF NOT EXISTS idx_allowance_bill
    ON Agreement_allowance_history (bill_nbr);

CREATE INDEX IF NOT EXISTS idx_bill_transaction
    ON Agreement_bill_history (transacion_id);

CREATE INDEX IF NOT EXISTS idx_journal_transaction
    ON Agreement_journal_history (transacion_id);

CREATE INDEX IF NOT EXISTS idx_sales_item_store_date
    ON Sales_item_store_history (item_nbr, store_nbr, sales_date);

CREATE INDEX IF NOT EXISTS idx_receivings_po_item
    ON Receivings_item_warehouse_history (purchase_order_id, item_nbr);
