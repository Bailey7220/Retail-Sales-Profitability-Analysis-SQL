WITH return_summary AS (
    SELECT
        OrderID,
        OrderLineID,
        SUM(QuantityReturned) AS quantity_returned
    FROM returns
    GROUP BY
        OrderID,
        OrderLineID
)
SELECT
    o.Channel,
    COUNT(DISTINCT o.OrderID) AS total_orders,
    SUM(o.Quantity) AS units_sold,
    COALESCE(SUM(r.quantity_returned), 0) AS units_returned,
    ROUND(
        100.0 * COALESCE(SUM(r.quantity_returned), 0)
        / NULLIF(SUM(o.Quantity), 0),
        2
    ) AS return_rate_pct,
    ROUND(SUM(o.NetRevenue), 2) AS net_revenue,
    ROUND(SUM(o.GrossProfit), 2) AS gross_profit,
    ROUND(
        100.0 * SUM(o.GrossProfit) / NULLIF(SUM(o.NetRevenue), 0),
        2
    ) AS gross_margin_pct
FROM vw_orders_enriched AS o
LEFT JOIN return_summary AS r
    ON o.OrderID = r.OrderID
   AND o.OrderLineID = r.OrderLineID
GROUP BY
    o.Channel
ORDER BY
    net_revenue DESC;