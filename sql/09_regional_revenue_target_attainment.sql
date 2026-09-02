WITH monthly_region_sales AS (
    SELECT
        date(OrderDate, 'start of month') AS month,
        Region,
        ROUND(SUM(NetRevenue), 2) AS actual_net_revenue
    FROM vw_orders_enriched
    WHERE Region <> 'Unassigned'
    GROUP BY
        date(OrderDate, 'start of month'),
        Region
)
SELECT
    mrs.month,
    mrs.Region,
    mrs.actual_net_revenue,
    ROUND(st.RevenueTarget, 2) AS revenue_target,
    ROUND(
        mrs.actual_net_revenue - st.RevenueTarget,
        2
    ) AS variance_to_target,
    ROUND(
        100.0 * mrs.actual_net_revenue
        / NULLIF(st.RevenueTarget, 0),
        2
    ) AS target_attainment_pct,
    CASE
        WHEN mrs.actual_net_revenue >= st.RevenueTarget
            THEN 'Met or Exceeded Target'
        ELSE 'Below Target'
    END AS target_status
FROM monthly_region_sales AS mrs
INNER JOIN sales_targets AS st
    ON mrs.month = st.Month
   AND mrs.Region = st.Region
ORDER BY
    mrs.month,
    mrs.Region;