#!/usr/bin/env bash
set -euo pipefail

# Registers a Debezium Postgres connector for the outbox_events and orders tables.
# Usage: ./scripts/register_connector.sh [name]

CONNECT_URL=${CONNECT_URL:-http://localhost:8083}
NAME=${1:-orders-outbox-connector}

echo "Registering connector $NAME at $CONNECT_URL"

curl -s -X PUT "$CONNECT_URL/connectors/$NAME/config" \
  -H 'Content-Type: application/json' \
  -d '{
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "plugin.name": "pgoutput",
    "database.hostname": "db",
    "database.port": "5432",
    "database.user": "appuser",
    "database.password": "apppass",
    "database.dbname": "appdb",
    "topic.prefix": "dbserver1",
    "schema.include.list": "public",
    "table.include.list": "public.outbox_events,public.orders",
    "slot.name": "orders_slot",
    "publication.autocreate.mode": "filtered",
    "tombstones.on.delete": "false",
    "snapshot.mode": "initial",
    "decimal.handling.mode": "double",
    "heartbeat.interval.ms": "5000",
    "include.schema.changes": "false"
  }' | jq . || echo "(Install jq for pretty JSON output)"

echo "Done. Check status: curl -s $CONNECT_URL/connectors/$NAME/status | jq ."
