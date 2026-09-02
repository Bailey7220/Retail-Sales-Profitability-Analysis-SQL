# Database Schema

## Overview

This project analyzes a synthetic multi-channel retail dataset using
seven related tables. The data model includes one primary transaction
table (`orders`) and supporting customer, product, store, return,
sales-target, and date-reference tables.

## Tables

| Table | Role | Description |
|---|---|---|
| `orders` | Fact table | Transactional order-line sales data; one row represents one product line within an order |
| `customers` | Dimension table | Customer attributes and segmentation details |
| `products` | Dimension table | Product, category, subcategory, cost, price, and supplier details |
| `stores` | Dimension table | Store, location, region, format, and opening-date details |
| `returns` | Fact table | Returned order-line quantities, dates, and return reasons |
| `sales_targets` | Fact table | Monthly revenue targets by region |
| `date_reference` | Date dimension | Calendar attributes used for time-based analysis |

## Key Relationships

```text
orders.CustomerID → customers.CustomerID
orders.ProductID → products.ProductID
orders.StoreID → stores.StoreID
orders.OrderDate → date_reference.Date

returns.OrderID + returns.OrderLineID
    → orders.OrderID + orders.OrderLineID

sales_targets.Month + sales_targets.Region
    → monthly order revenue grouped by month and store region
```

## Important Business Definitions

- **Gross Revenue:** Quantity sold multiplied by unit price before discounts.
- **Net Revenue:** Gross revenue minus the discount amount.
- **Cost of Goods Sold (COGS):** Quantity sold multiplied by product unit cost.
- **Gross Profit:** Net revenue minus COGS.
- **Gross Margin %:** Gross profit divided by net revenue.
- **Return Rate %:** Returned quantity divided by quantity sold.
- **Revenue Target Attainment %:** Actual net revenue divided by the monthly regional revenue target.

## Data Scope and Limitation

The dataset is synthetic and was created for portfolio and educational
purposes. It does not represent a real retailer, real customers, or
employer data. Results demonstrate SQL analysis and business-reporting
methodology rather than actual business performance.
