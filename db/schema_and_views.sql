
-- DDL for ecommerce BI project
CREATE TABLE dim_customer (
  customer_id INTEGER PRIMARY KEY,
  signup_date DATE,
  region TEXT,
  country TEXT,
  segment TEXT
);

CREATE TABLE fact_marketing (
  date DATE,
  region TEXT,
  channel TEXT,
  spend NUMERIC,
  sessions INTEGER
);

CREATE TABLE fact_orders (
  order_id INTEGER PRIMARY KEY,
  customer_id INTEGER,
  order_date DATE,
  ship_date DATE,
  delivery_date DATE,
  promised_delivery_date DATE,
  region TEXT,
  country TEXT,
  channel TEXT,
  items INTEGER,
  revenue NUMERIC,
  cogs NUMERIC,
  returned_flag BOOLEAN
);

CREATE TABLE fact_returns (
  return_id INTEGER PRIMARY KEY,
  order_id INTEGER,
  return_date DATE,
  reason_code TEXT,
  refund_amount NUMERIC
);

-- Views for analytics
-- Daily revenue
CREATE VIEW vw_daily_revenue AS
SELECT order_date AS date, region, country, SUM(revenue) AS revenue, COUNT(*) AS orders
FROM fact_orders
GROUP BY 1,2,3;

-- On-time delivery percentage by day
CREATE VIEW vw_otd AS
SELECT order_date AS date, region,
       SUM(CASE WHEN delivery_date <= promised_delivery_date THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 AS otd_pct
FROM fact_orders
GROUP BY 1,2;

-- New customers per month
CREATE VIEW vw_new_customers AS
WITH first_orders AS (
  SELECT customer_id, MIN(order_date) AS first_date
  FROM fact_orders
  GROUP BY 1
)
SELECT DATE_TRUNC('month', first_date) AS month, COUNT(*) AS new_customers
FROM first_orders
GROUP BY 1
ORDER BY 1;

-- Return rate by month
CREATE VIEW vw_return_rate_month AS
SELECT DATE_TRUNC('month', order_date) AS month, region,
       SUM(CASE WHEN returned_flag THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 AS return_rate_pct
FROM fact_orders
GROUP BY 1,2
ORDER BY 1,2;
