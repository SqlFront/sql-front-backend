\connect users_db;

-- Allow user_events without a task_id for general auth/platform events
ALTER TABLE public.user_events ALTER COLUMN task_id DROP NOT NULL;
