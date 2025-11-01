#!/usr/bin/env bash
set -euo pipefail
# Quick environment diagnostic

echo "== Postgres replication settings =="
docker compose exec -T db psql -U appuser -d appdb -c "select name,setting from pg_settings where name in ('wal_level','max_replication_slots','max_wal_senders');" || true

echo "\n== Kafka broker metadata =="
docker compose exec -T kafka kafka-broker-api-versions --bootstrap-server kafka:29092 | head -n 20 || true

echo "\n== Existing topics (filtered) =="
docker compose exec -T kafka kafka-topics --bootstrap-server kafka:29092 --list | grep -E 'outbox|orders' || true

echo "\n== Connector status =="
curl -s http://localhost:8083/connectors/orders-outbox-connector/status | jq '.state? // .connector?.state // .connector?.state // "(not found)"'
