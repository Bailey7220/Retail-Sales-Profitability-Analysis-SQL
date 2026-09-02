SELECT
    COUNT(DISTINCT OrderID) AS total_orders,
    COUNT(*) AS order_lines,
    COUNT(DISTINCT CustomerID) AS unique_customers,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(GrossRevenue), 2) AS gross_revenue,
    ROUND(SUM(DiscountAmount), 2) AS total_discounts,
    ROUND(SUM(NetRevenue), 2) AS net_revenue,
    ROUND(SUM(COGS), 2) AS total_cogs,
    ROUND(SUM(GrossProfit), 2) AS gross_profit,
    ROUND(
        100.0 * SUM(GrossProfit) / NULLIF(SUM(NetRevenue), 0),
        2
    ) AS gross_margin_pct,
    ROUND(
        SUM(NetRevenue) / NULLIF(COUNT(DISTINCT OrderID), 0),
        2
    ) AS average_order_value
FROM vw_orders_enriched;