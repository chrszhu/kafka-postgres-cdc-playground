-- Core tables
CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id UUID PRIMARY KEY,
  customer_id INT NOT NULL REFERENCES customers(id),
  amount_cents INT NOT NULL,
  status TEXT NOT NULL DEFAULT 'PENDING',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Outbox table for reliable event publication
CREATE TABLE IF NOT EXISTS outbox_events (
  id UUID PRIMARY KEY,
  aggregate_type TEXT NOT NULL,
  aggregate_id TEXT NOT NULL,
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  published BOOLEAN NOT NULL DEFAULT false
);

-- Projection / materialized view target
CREATE TABLE IF NOT EXISTS order_totals (
  customer_id INT PRIMARY KEY,
  total_amount_cents BIGINT NOT NULL,
  order_count INT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO customers(name) VALUES ('Alice'), ('Bob'), ('Carol');
