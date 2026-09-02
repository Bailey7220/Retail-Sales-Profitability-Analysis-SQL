SELECT
    Category,
    SUM(Quantity) AS units_sold,
    ROUND(SUM(NetRevenue), 2) AS net_revenue,
    ROUND(SUM(GrossProfit), 2) AS gross_profit,
    ROUND(
        100.0 * SUM(GrossProfit) / NULLIF(SUM(NetRevenue), 0),
        2
    ) AS gross_margin_pct,
    RANK() OVER (
        ORDER BY SUM(NetRevenue) DESC
    ) AS revenue_rank,
    RANK() OVER (
        ORDER BY SUM(GrossProfit) DESC
    ) AS gross_profit_rank
FROM vw_orders_enriched
GROUP BY
    Category
ORDER BY
    net_revenue DESC;