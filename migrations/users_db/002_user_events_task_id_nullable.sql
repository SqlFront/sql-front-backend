-- TimescaleDB requires the partition column in a primary key. Replace the
-- legacy key containing task_id before allowing taskless auth events.
DO $$
DECLARE
    old_primary_key text;
BEGIN
    SELECT constraint_name.conname INTO old_primary_key
    FROM pg_constraint AS constraint_name
    JOIN pg_attribute AS column_name
      ON column_name.attrelid = constraint_name.conrelid
     AND column_name.attnum = ANY(constraint_name.conkey)
    WHERE constraint_name.conrelid = 'public.user_events'::regclass
      AND constraint_name.contype = 'p'
      AND column_name.attname = 'task_id';

    IF old_primary_key IS NOT NULL THEN
        EXECUTE format('ALTER TABLE public.user_events DROP CONSTRAINT %I', old_primary_key);
        ALTER TABLE public.user_events
            ADD CONSTRAINT user_events_pkey PRIMARY KEY (id, "timestamp");
    END IF;
END $$;

ALTER TABLE public.user_events ALTER COLUMN task_id DROP NOT NULL;
