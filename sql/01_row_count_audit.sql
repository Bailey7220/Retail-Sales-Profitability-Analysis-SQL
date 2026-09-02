SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM customers

UNION ALL

SELECT 'date_reference' AS table_name, COUNT(*) AS row_count
FROM date_reference

UNION ALL

SELECT 'orders' AS table_name, COUNT(*) AS row_count
FROM orders

UNION ALL

SELECT 'products' AS table_name, COUNT(*) AS row_count
FROM products

UNION ALL

SELECT 'returns' AS table_name, COUNT(*) AS row_count
FROM returns

UNION ALL

SELECT 'sales_targets' AS table_name, COUNT(*) AS row_count
FROM sales_targets

UNION ALL

SELECT 'stores' AS table_name, COUNT(*) AS row_count
FROM stores;