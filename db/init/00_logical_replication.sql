-- Ensure logical replication parameters for Debezium
-- Executed only on first cluster initialization (docker volume fresh).
ALTER SYSTEM SET wal_level = 'logical';
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET max_connections = 100;
-- Apply (some settings need restart; since this runs at init, next start already has them)
SELECT 'logical replication settings applied' AS info;
