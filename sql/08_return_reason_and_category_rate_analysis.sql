-- Return reason volume by product category.
-- Note: This query identifies return-volume drivers. Its percentage is
-- calculated only within returned records and is not an overall return rate.

SELECT
    o.Category,
    r.ReturnReason,
    COUNT(*) AS return_records,
    SUM(r.QuantityReturned) AS units_returned
FROM returns AS r
INNER JOIN vw_orders_enriched AS o
    ON r.OrderID = o.OrderID
   AND r.OrderLineID = o.OrderLineID
GROUP BY
    o.Category,
    r.ReturnReason
ORDER BY
    units_returned DESC,
    o.Category,
    r.ReturnReason;


-- True category return rate: returned units divided by all units sold.

WITH category_sales AS (
    SELECT
        Category,
        SUM(Quantity) AS units_sold
    FROM vw_orders_enriched
    GROUP BY
        Category
),
category_returns AS (
    SELECT
        o.Category,
        SUM(r.QuantityReturned) AS units_returned
    FROM returns AS r
    INNER JOIN vw_orders_enriched AS o
        ON r.OrderID = o.OrderID
       AND r.OrderLineID = o.OrderLineID
    GROUP BY
        o.Category
)
SELECT
    cs.Category,
    cs.units_sold,
    COALESCE(cr.units_returned, 0) AS units_returned,
    ROUND(
        100.0 * COALESCE(cr.units_returned, 0)
        / NULLIF(cs.units_sold, 0),
        2
    ) AS true_return_rate_pct
FROM category_sales AS cs
LEFT JOIN category_returns AS cr
    ON cs.Category = cr.Category
ORDER BY
    true_return_rate_pct DESC;