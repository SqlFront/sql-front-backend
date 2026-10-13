-- Migration 001 for game_db: Equipment audit and permissions for PL/pgSQL
CREATE TABLE IF NOT EXISTS public.equipment_audit (
    id SERIAL PRIMARY KEY,
    item_name character varying NOT NULL,
    added_at date DEFAULT CURRENT_DATE
);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sql_runner') THEN
        EXECUTE 'GRANT CREATE, USAGE ON SCHEMA public TO sql_runner';
        EXECUTE 'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sql_runner';
        EXECUTE 'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sql_runner';
        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sql_runner';
        EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sql_runner';
    END IF;
END $$;
