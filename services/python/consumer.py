import os, json, time
from datetime import datetime
import psycopg
from kafka import KafkaConsumer

BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
DB_URL = os.getenv('DATABASE_URL', 'postgresql://appuser:apppass@localhost:5432/appdb')
OUTBOX_TOPIC = 'outbox.events'
GROUP_ID = 'order-aggregator'

consumer = KafkaConsumer(
    OUTBOX_TOPIC,
    bootstrap_servers=BOOTSTRAP,
    group_id=GROUP_ID,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda b: json.loads(b.decode('utf-8'))
)

UPSERT_SQL = """
INSERT INTO order_totals (customer_id, total_amount_cents, order_count, updated_at)
VALUES (%s, %s, %s, %s)
ON CONFLICT (customer_id)
DO UPDATE SET total_amount_cents = EXCLUDED.total_amount_cents,
              order_count = EXCLUDED.order_count,
              updated_at = EXCLUDED.updated_at;
"""

SELECT_SQL = "SELECT total_amount_cents, order_count FROM order_totals WHERE customer_id=%s"


def process_event(conn, evt):
    customer_id = evt['customer_id']
    amount = evt['amount_cents']
    with conn.cursor() as cur:
        cur.execute(SELECT_SQL, (customer_id,))
        row = cur.fetchone()
        if row:
            total, count = row
            total += amount
            count += 1
        else:
            total, count = amount, 1
        cur.execute(UPSERT_SQL, (customer_id, total, count, datetime.utcnow()))
    conn.commit()


def main():
    with psycopg.connect(DB_URL) as conn:
        print('Consumer started. Listening for events...')
        for msg in consumer:
            evt = msg.value
            try:
                process_event(conn, evt)
                print('Aggregated customer', evt['customer_id'], 'amount', evt['amount_cents'])
            except Exception as e:
                print('Error processing event', e)
                time.sleep(1)

if __name__ == '__main__':
    main()
