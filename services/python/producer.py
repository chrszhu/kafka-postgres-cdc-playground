import os, time, uuid, random, json
from datetime import datetime
import psycopg
from kafka import KafkaProducer

BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
DB_URL = os.getenv('DATABASE_URL', 'postgresql://appuser:apppass@localhost:5432/appdb')
OUTBOX_TOPIC = 'outbox.events'

producer = KafkaProducer(bootstrap_servers=BOOTSTRAP, value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def insert_order_and_outbox(conn):
    with conn.cursor() as cur:
        order_id = str(uuid.uuid4())
        customer_id = random.choice([1,2,3])
        amount_cents = random.randint(500, 5000)
        payload = {
            'order_id': order_id,
            'customer_id': customer_id,
            'amount_cents': amount_cents,
            'status': 'PENDING',
            'ts': datetime.utcnow().isoformat()
        }
        # Insert order row
        cur.execute("INSERT INTO orders (id, customer_id, amount_cents, status) VALUES (%s,%s,%s,%s)", (order_id, customer_id, amount_cents, 'PENDING'))
        # Insert outbox event row (Debezium will capture)
        cur.execute("INSERT INTO outbox_events (id, aggregate_type, aggregate_id, type, payload) VALUES (%s,%s,%s,%s,%s)", (str(uuid.uuid4()), 'Order', order_id, 'OrderCreated', json.dumps(payload)))
    conn.commit()
    return payload

def fallback_direct_publish(event):
    # Direct publish if you want immediate event (parallel to outbox CDC)
    producer.send(OUTBOX_TOPIC, event)


def main():
    with psycopg.connect(DB_URL, autocommit=False) as conn:
        print('Producer connected. Generating orders...')
        while True:
            evt = insert_order_and_outbox(conn)
            print('Inserted order + outbox', evt)
            # Optional: also publish directly
            fallback_direct_publish(evt)
            time.sleep(2)

if __name__ == '__main__':
    main()
