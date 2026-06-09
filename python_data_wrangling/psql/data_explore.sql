-- Show table schema
\d+ retail;

-- Show first 10 rows
SELECT *
FROM retail
LIMIT 10;

-- Check number of records
SELECT COUNT(*)
FROM retail;

-- Number of clients (unique customer IDs)
SELECT COUNT(DISTINCT customer_id)
FROM retail;

-- Invoice date range
SELECT
    MIN(invoice_date) AS min_invoice_date,
    MAX(invoice_date) AS max_invoice_date
FROM retail;

-- Number of SKUs / products (unique stock codes)
SELECT COUNT(DISTINCT stock_code)
FROM retail;

-- Calculate average invoice amount excluding invoices
-- with a negative total amount (e.g. canceled orders)
SELECT AVG(invoice_total) AS avg_invoice_amount
FROM (
    SELECT
        invoice_no,
        SUM(unit_price * quantity) AS invoice_total
    FROM retail
    GROUP BY invoice_no
    HAVING SUM(unit_price * quantity) > 0
) AS t;

-- Calculate total revenue
SELECT SUM(unit_price * quantity) AS total_revenue
FROM retail;

-- Calculate total revenue by YYYYMM
SELECT
    CAST(EXTRACT(YEAR FROM invoice_date) AS INTEGER) * 100 +
    CAST(EXTRACT(MONTH FROM invoice_date) AS INTEGER) AS yyyymm,
    SUM(unit_price * quantity) AS revenue
FROM retail
GROUP BY yyyymm
ORDER BY yyyymm;
