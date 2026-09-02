SELECT
    'Missing customer matches' AS check_name,
    COUNT(*) AS issue_count
FROM orders AS o
LEFT JOIN customers AS c
    ON o.CustomerID = c.CustomerID
WHERE c.CustomerID IS NULL

UNION ALL

SELECT
    'Missing product matches' AS check_name,
    COUNT(*) AS issue_count
FROM orders AS o
LEFT JOIN products AS p
    ON o.ProductID = p.ProductID
WHERE p.ProductID IS NULL

UNION ALL

SELECT
    'Missing store matches' AS check_name,
    COUNT(*) AS issue_count
FROM orders AS o
LEFT JOIN stores AS s
    ON o.StoreID = s.StoreID
WHERE s.StoreID IS NULL;