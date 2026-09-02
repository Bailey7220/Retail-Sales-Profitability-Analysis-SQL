WITH product_sales AS (
    SELECT
        ProductID,
        ProductName,
        Category,
        Supplier,
        SUM(Quantity) AS units_sold,
        ROUND(SUM(NetRevenue), 2) AS net_revenue,
        ROUND(SUM(GrossProfit), 2) AS gross_profit,
        ROUND(
            100.0 * SUM(GrossProfit) / NULLIF(SUM(NetRevenue), 0),
            2
        ) AS gross_margin_pct
    FROM vw_orders_enriched
    GROUP BY
        ProductID,
        ProductName,
        Category,
        Supplier
),
product_returns AS (
    SELECT
        o.ProductID,
        SUM(r.QuantityReturned) AS units_returned
    FROM returns AS r
    INNER JOIN vw_orders_enriched AS o
        ON r.OrderID = o.OrderID
       AND r.OrderLineID = o.OrderLineID
    GROUP BY
        o.ProductID
)
SELECT
    ps.ProductID,
    ps.ProductName,
    ps.Category,
    ps.Supplier,
    ps.units_sold,
    COALESCE(pr.units_returned, 0) AS units_returned,
    ROUND(
        100.0 * COALESCE(pr.units_returned, 0)
        / NULLIF(ps.units_sold, 0),
        2
    ) AS return_rate_pct,
    ps.net_revenue,
    ps.gross_profit,
    ps.gross_margin_pct
FROM product_sales AS ps
LEFT JOIN product_returns AS pr
    ON ps.ProductID = pr.ProductID
WHERE ps.net_revenue >= 150000
ORDER BY
    return_rate_pct DESC,
    ps.net_revenue DESC;