WITH monthly_performance AS (
    SELECT
        strftime('%Y-%m', OrderDate) AS month,
        COUNT(DISTINCT OrderID) AS total_orders,
        SUM(Quantity) AS units_sold,
        ROUND(SUM(NetRevenue), 2) AS net_revenue,
        ROUND(SUM(GrossProfit), 2) AS gross_profit,
        ROUND(
            100.0 * SUM(GrossProfit) / NULLIF(SUM(NetRevenue), 0),
            2
        ) AS gross_margin_pct
    FROM vw_orders_enriched
    GROUP BY
        strftime('%Y-%m', OrderDate)
)
SELECT
    month,
    total_orders,
    units_sold,
    net_revenue,
    gross_profit,
    gross_margin_pct,
    ROUND(
        SUM(net_revenue) OVER (
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ),
        2
    ) AS running_net_revenue
FROM monthly_performance
ORDER BY
    month;