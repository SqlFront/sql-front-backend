#!/bin/bash
set -e

restore_backup_if_exists() {
    local db=$1

    for backup_path in "/backups/$db.sql" "/backups/backups/$db.sql"; do
        if [ -f "$backup_path" ]; then
            echo "Restoring $db from SQL backup: $backup_path"
            psql -U "$POSTGRES_USER" -d "$db" -f "$backup_path"
            return 0
        fi
    done
}

create_db_with_timescale() {
    local db=$1
    echo "Creating database: $db"
    
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $db;
EOSQL

    echo "Enabling TimescaleDB extension for $db"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS timescaledb;
EOSQL

    restore_backup_if_exists "$db"
    
    echo "Creating analytics tables in $db"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$db" <<-EOSQL
    CREATE TABLE IF NOT EXISTS user_events (
        id BIGSERIAL,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        user_id INTEGER NOT NULL,
        task_id INTEGER,
        event_type TEXT NOT NULL,
        payload JSONB DEFAULT '{}'::jsonb
    );
    
    DO \$\$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'user_events_pkey'
        ) THEN
            ALTER TABLE user_events ADD PRIMARY KEY (user_id, task_id, timestamp);
        END IF;
    END \$\$;
    
    DO \$\$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'user_events'
        ) THEN
            PERFORM create_hypertable('user_events', 'timestamp');
        END IF;
    END \$\$;
    
    CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id);
    CREATE INDEX IF NOT EXISTS idx_user_events_task ON user_events(task_id) WHERE task_id IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);

    CREATE INDEX IF NOT EXISTS idx_user_events_time ON user_events(timestamp DESC);
EOSQL

}

create_db_with_timescale "users_db"

echo "Creating game_db and setting up restricted user"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE game_db;
    
    CREATE USER sql_runner WITH PASSWORD '${RUNNER_PASSWORD}';
    
    \c game_db
    
    GRANT CONNECT ON DATABASE game_db TO sql_runner;
    
    GRANT USAGE ON SCHEMA public TO sql_runner;
    
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO sql_runner;
    
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sql_runner;

EOSQL

restore_backup_if_exists "game_db"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d game_db <<-EOSQL
    GRANT CREATE, USAGE ON SCHEMA public TO sql_runner;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sql_runner;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sql_runner;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sql_runner;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sql_runner;
EOSQL


echo "Creating quest_db"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE quest_db;
    
    \c quest_db
    
    GRANT CONNECT ON DATABASE quest_db TO sql_runner;
    
    GRANT USAGE ON SCHEMA public TO sql_runner;
    
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO sql_runner;
    
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sql_runner;

EOSQL

restore_backup_if_exists "quest_db"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d quest_db <<-EOSQL
    GRANT USAGE ON SCHEMA public TO sql_runner;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sql_runner;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sql_runner;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sql_runner;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sql_runner;
EOSQL
