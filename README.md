# Kafka + Postgres CDC Playground

Hands‑on lab to learn end‑to‑end streaming with:
- PostgreSQL logical replication + Outbox pattern
- Debezium (Kafka Connect) Change Data Capture (CDC)
- Kafka topics (CDC envelopes vs direct app events)
- Python producer & consumer building a materialized projection
- Optional ksqlDB / future Kafka Streams extension

## Stack
- Docker Compose orchestrates services
- Apache Kafka (broker + Zookeeper)
- Kafka Connect (Debezium Postgres connector)
- PostgreSQL 15 (orders + outbox tables + projection table)
- Schema Registry (placeholder for future Avro use)
- Python producer & consumer containers (or run locally)
- Optional: ksqlDB server (enable via profile `ksql`)

## Learning Objectives
1. Capture DB changes as immutable Kafka events (CDC).
2. Compare direct app-produced JSON vs Debezium envelopes.
3. Build a read model (`order_totals`) from a stream.
4. Replay state by truncating and re-consuming.
5. Inspect replication artifacts (slot, publication) & message metadata.

## Services Overview
- db: primary Postgres OLTP (orders, order_items)
- connect: Kafka Connect + Debezium for CDC of public schema tables
- producer: simple Python app generating Orders
- consumer: Python app consuming enriched order events and writing aggregates
- streams-app: Java (Kafka Streams) performing join & aggregation (optional)
- schema-registry: Confluent Schema Registry (Avro serialization)

## Data Flow (simplified)
1. Producer inserts into Postgres (orders table) and also writes an outbox event (orders_outbox).
2. Debezium captures row-level changes -> emits to Kafka topics (dbserver1.public.orders, ... , outbox.events).
3. Streams app / ksqlDB transforms raw CDC events into domain events topic (orders.events.v1).
4. Consumer aggregates total order value per customer -> writes to table order_totals.

## Quick Start
Prereqs: Docker & Docker Compose, Java 17 (for Streams app), Python 3.11.

## Prerequisites
- Docker Desktop (or other Docker engine) running
- Python 3.11+ (if running producer/consumer locally)
- (Optional) `jq` for pretty JSON

## Fresh Setup (Clean Start)
```bash
git clone <this repo>  # if not already
cd kafka-playground
# 1. Start ONLY Postgres first time not required anymore; start full stack:
/scripts

# 2. Register Debezium connector (creates slot + publication + topics)
./scripts/register_connector.sh   # or: bash scripts/register_connector.sh

# 3. Verify connector RUNNING
curl -s http://localhost:8083/connectors/orders-outbox-connector/status

# 4. List topics (should see dbserver1.public.* after first inserts)
  register_connector.sh

# 5. (Optional) Run producer locally instead of container
pip install -r services/python/requirements.txt
python services/python/producer.py

# 6. (Optional) Run consumer locally
python services/python/consumer.py
```

The included producer/consumer containers also start automatically (see `docker compose ps`).

## Verifying CDC Works
1. Confirm Postgres replication settings:
```bash
/db
```
Expect: `logical`.
2. Check replication slot & publication:
```bash
  init
    01_schema.sql
```
3. Insert order (if producer not running):
```bash
    02_seed.sql
```
4. Consume a CDC message:
```bash
/services
  python
```
Look for JSON with `op":"c"` (create) and metadata block `source`.

## Producer & Consumer (Local vs Container)
Container mode (already running):
```bash
    requirements.txt
docker compose logs -f consumer | head
```
Local mode (stop containerized ones first if you wish):
```bash
    producer.py
python services/python/producer.py
python services/python/consumer.py
```

## Aggregation & Replay
Projection table: `order_totals` (sum + count per customer).
Inspect:
```bash
    consumer.py
```
Replay (rebuild from earliest offsets):
```bash
  streams-app
python services/python/consumer.py   # restart consumer; it will re-consume
```

## Key Topics
| Purpose | Topic |
|---------|-------|
| Debezium CDC orders | `dbserver1.public.orders` |
| Debezium CDC outbox | `dbserver1.public.outbox_events` |
| Heartbeat | `__debezium-heartbeat.dbserver1` |
| Connect internal | `connect-configs`, `connect-offsets`, `connect-status` |
| Direct published events (bypass CDC) | `outbox.events` |

## Scripts
| Script | Purpose |
|--------|---------|
| `scripts/register_connector.sh` | Registers Debezium Postgres connector |
| `scripts/check_env.sh` | Quick diagnostic (replication settings, topics, connector) |

## Common Commands Cheat Sheet
```bash
# Show running services
    build.gradle
# List topics (all)
    settings.gradle
# Consume N CDC messages
    src/main/java/... (Streams code)
```
# View connector status

# DB psql shell
## Next Steps / Exercises
```

## Troubleshooting
| Symptom | Check / Fix |
|---------|-------------|
| Connector 400: wal_level must be logical | Ensure `db` service includes the `command` with `wal_level=logical`; `docker compose down -v && up -d` |
| No `dbserver1.public.*` topics | Insert a new row; ensure connector RUNNING; list topics without grep |
| Connect logs show broker errors | Ensure `KAFKA_LISTENERS` & `KAFKA_ADVERTISED_LISTENERS` both set; restart kafka & connect |
| Projection not updating | Confirm consumer running; check its stdout/logs; ensure topic offsets not exhausted |
| Want a clean slate | `docker compose down -v` removes volumes (loses DB data) |
| Disk bloat during experimentation | `docker system prune -f` |

Detailed manual steps for Docker Desktop hiccups & Debezium snapshot issues are also summarized inside the troubleshooting section above.

## Extending the Playground
Short next-task ideas:
1. Remove direct publish to `outbox.events` and derive everything from CDC.
2. Introduce Avro + Schema Registry (switch producer serializer & consumer deserializer).
3. Add Kafka Streams / ksqlDB to project a cleaner `orders.events.v1` topic.
4. Add a dead-letter topic for consumer failures.
5. Add a replay script that rebuilds `order_totals` purely from CDC topics.
6. Add tests (Python) for aggregation logic (idempotency / replay).

## Cleanup
```bash
- Add schema evolution (alter orders table, update Avro schema).
- Add dead letter topic handling.
- Switch broker to KRaft mode (remove Zookeeper).
```

## License
MIT
- Replace Python consumer with Materialize or ClickHouse sink.

## License
MIT
