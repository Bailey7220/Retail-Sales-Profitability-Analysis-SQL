DROP VIEW IF EXISTS vw_orders_enriched;

CREATE VIEW vw_orders_enriched AS
SELECT
    o.OrderID,
    o.OrderLineID,
    o.OrderDate,
    o.CustomerID,
    TRIM(c.FirstName || ' ' || c.LastName) AS CustomerName,
    c.MembershipTier,
    c.State AS CustomerState,
    c.SignupDate,
    o.ProductID,
    p.ProductName,
    p.Category,
    p.SubCategory,
    p.Supplier,
    o.StoreID,
    COALESCE(s.StoreName, 'Unassigned Store') AS StoreName,
    COALESCE(s.City, 'Unassigned') AS StoreCity,
    COALESCE(s.State, 'Unassigned') AS StoreState,
    COALESCE(s.Region, 'Unassigned') AS Region,
    COALESCE(s.StoreType, 'Unassigned') AS StoreType,
    o.Channel,
    o.ShipStateRaw,
    o.Quantity,
    o.UnitPrice,
    o.DiscountPct,
    p.UnitCost,
    ROUND(o.Quantity * o.UnitPrice, 2) AS GrossRevenue,
    ROUND(
        o.Quantity * o.UnitPrice * o.DiscountPct,
        2
    ) AS DiscountAmount,
    ROUND(
        (o.Quantity * o.UnitPrice)
        - (o.Quantity * o.UnitPrice * o.DiscountPct),
        2
    ) AS NetRevenue,
    ROUND(
        o.Quantity * p.UnitCost,
        2
    ) AS COGS,
    ROUND(
        (
            (o.Quantity * o.UnitPrice)
            - (o.Quantity * o.UnitPrice * o.DiscountPct)
        )
        - (o.Quantity * p.UnitCost),
        2
    ) AS GrossProfit
FROM orders AS o
LEFT JOIN customers AS c
    ON o.CustomerID = c.CustomerID
LEFT JOIN products AS p
    ON o.ProductID = p.ProductID
LEFT JOIN stores AS s
    ON o.StoreID = s.StoreID;
